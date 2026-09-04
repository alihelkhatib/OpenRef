#include <stdbool.h>
#include <stdint.h>
#include "app.h"
#include "board.h"
#include "fsl_clock.h"
#include "fsl_ctimer.h"
#include "fsl_debug_console.h"
#include "flash_config.h"
#include "openref_audio_runtime.h"
#include "openref_rt595_audio_io_mcux.h"
#include "openref_rt595_board_resources.h"
#include "openref_rt595_audio_spi_mcux.h"
#include "openref_rt595_lc3.h"
#include "openref_rt595_output_guard.h"
#include "openref_rt595_watchdog.h"
#include "openref_rt595_app_confirmation.h"
#include "openref_rt595_boot_state_mcux.h"
#include "openref_rt595_update_crypto_mcux.h"
#include "openref_rt595_update_delivery.h"
#include "openref_rt595_update_staging_mcux.h"
#include "openref_rt595_integrated_update.h"
#if defined(OPENREF_HAS_TRUST_ANCHOR)
#include "openref_trust_anchor_generated.h"
#endif

#if !defined(OPENREF_CURRENT_SLOT) || OPENREF_CURRENT_SLOT > 1
#error "OPENREF_CURRENT_SLOT must identify slot A (0) or B (1)"
#endif
#if !defined(OPENREF_IMAGE_VERSION) || OPENREF_IMAGE_VERSION < 1
#error "OPENREF_IMAGE_VERSION must match the signed image manifest"
#endif

#define OPENREF_SLOT_A_IMAGE 0x08041000u
#define OPENREF_SLOT_A_MANIFEST 0x08040000u
#define OPENREF_SLOT_B_IMAGE 0x08101000u
#define OPENREF_SLOT_B_MANIFEST 0x08100000u
#define OPENREF_SLOT_CAPACITY 0x000bf000u
#define OPENREF_BOOT_STATE_BASE 0x081fe000u
#define OPENREF_FLASH_END 0x08200000u
#define OPENREF_HARDWARE_ID 0x59500001u
#define OPENREF_BOOTLOADER_VERSION 1u
#define OPENREF_UPDATE_TIMEOUT_US 5000000u

_Static_assert(BOARD_DEBUG_UART_INSTANCE == OPENREF_RT595_FLEXCOMM_DEBUG,
               "EVK debug-console Flexcomm changed");
_Static_assert(DEMO_DMIC_RX_CHANNEL == OPENREF_RT595_DMA_DMIC_RX,
               "EVK DMIC DMA channel changed");
_Static_assert(DEMO_I2S_TX_CHANNEL == OPENREF_RT595_DMA_I2S_TX,
               "EVK I2S DMA channel changed");
#include "openref_watchdog_gate.h"

static openref_audio_runtime_t runtime;
static openref_rt595_lc3_t codec;
static openref_rt595_audio_io_mcux_t audio_io;
static openref_rt595_audio_spi_mcux_t audio_spi;
static openref_watchdog_gate_t watchdog_gate;
static openref_rt595_output_guard_t output_guard;
static bool watchdog_ready;
static openref_rt595_boot_state_mcux_t confirmation_boot_state;
static openref_rt595_app_confirmation_t confirmation;
static bool confirmation_active;
static openref_rt595_update_crypto_mcux_t update_crypto;
static openref_rt595_update_staging_mcux_t update_stage[2];
static openref_rt595_update_delivery_t update_delivery;
static bool update_ready;
extern const flexspi_nor_config_t flash_config;

static bool address_in_running_slot(uintptr_t address)
{
    const uintptr_t base = OPENREF_CURRENT_SLOT == 0 ? OPENREF_SLOT_A_IMAGE : OPENREF_SLOT_B_IMAGE;
    return address >= base && address < base + OPENREF_SLOT_CAPACITY;
}

static bool confirmation_storage_init(void)
{
    const uintptr_t expected_base = OPENREF_CURRENT_SLOT == 0 ? OPENREF_SLOT_A_IMAGE : OPENREF_SLOT_B_IMAGE;
    openref_boot_slot_t slots[2] = {{0}};
    flexspi_nor_config_t *config = (flexspi_nor_config_t *)(uintptr_t)&flash_config;
    /* Refuse even to initialize a writable backend in a development/bootstrap
     * image or a binary built for the other slot. */
    if ((uintptr_t)SCB->VTOR != expected_base ||
        !address_in_running_slot((uintptr_t)&confirmation_storage_init)) return false;
    if (!openref_rt595_boot_state_mcux_init(&confirmation_boot_state, config, 0u,
            OPENREF_BOOT_STATE_BASE, OPENREF_BOOT_STATE_BASE, OPENREF_FLASH_END) ||
        !openref_rt595_boot_state_load(&confirmation_boot_state.store)) return false;
    if (confirmation_boot_state.store.state.pending_slot != OPENREF_CURRENT_SLOT ||
        confirmation_boot_state.store.state.pending_attempts == 0u ||
        confirmation_boot_state.store.state.confirmed_slot == OPENREF_CURRENT_SLOT) {
        confirmation_active = false;
        return true;
    }
    slots[OPENREF_CURRENT_SLOT] = (openref_boot_slot_t){true, true, OPENREF_IMAGE_VERSION};
    confirmation_active = openref_rt595_app_confirmation_init(&confirmation,
        &confirmation_boot_state.store, OPENREF_CURRENT_SLOT, slots);
    return confirmation_active;
}

static bool activate_candidate(void *context, uint8_t slot, uint32_t version)
{
    openref_rt595_boot_state_store_t *store = context;
    openref_boot_slot_t slots[2] = {{0}};
    slots[OPENREF_CURRENT_SLOT] = (openref_boot_slot_t){true, true, OPENREF_IMAGE_VERSION};
    slots[slot] = (openref_boot_slot_t){true, true, version};
    return openref_rt595_boot_state_stage(store, slot, slots);
}

static bool update_delivery_init(void)
{
#if defined(OPENREF_HAS_TRUST_ANCHOR)
    flexspi_nor_config_t *config = (flexspi_nor_config_t *)(uintptr_t)&flash_config;
    uint32_t floor = confirmation_boot_state.store.state.minimum_version;
    if (floor < OPENREF_IMAGE_VERSION) floor = OPENREF_IMAGE_VERSION;
    const openref_update_platform_t platform = {
        OPENREF_UPDATE_TARGET_AUDIO, OPENREF_HARDWARE_ID,
        OPENREF_BOOTLOADER_VERSION, floor, floor, OPENREF_SLOT_CAPACITY
    };
    return openref_rt595_update_crypto_mcux_init(&update_crypto,
               openref_trust_anchor_key_id, openref_trust_anchor_public_key) &&
        openref_rt595_update_staging_mcux_init(&update_stage[0], 0u, config,
            OPENREF_FLASH_END, OPENREF_SLOT_A_MANIFEST,
            OPENREF_SLOT_A_IMAGE, OPENREF_SLOT_CAPACITY) &&
        openref_rt595_update_staging_mcux_init(&update_stage[1], 0u, config,
            OPENREF_FLASH_END, OPENREF_SLOT_B_MANIFEST,
            OPENREF_SLOT_B_IMAGE, OPENREF_SLOT_CAPACITY) &&
        openref_rt595_update_delivery_init(&update_delivery,
            &update_stage[0].staging, &update_stage[1].staging,
            OPENREF_CURRENT_SLOT,
            OPENREF_CURRENT_SLOT == 0 ? OPENREF_SLOT_A_IMAGE : OPENREF_SLOT_B_IMAGE,
            OPENREF_SLOT_CAPACITY, OPENREF_UPDATE_TIMEOUT_US, &platform,
            openref_rt595_update_crypto_callbacks(&update_crypto.crypto),
            activate_candidate, &confirmation_boot_state.store);
#else
    return false;
#endif
}

/* Trusted command-demultiplexer boundary.  The transport must authenticate
 * and authorize its peer before calling these functions; this layer owns all
 * ordering, bounds, inactive-slot, signature, digest, and durable-activation
 * enforcement after that boundary. */
openref_rt595_update_delivery_result_t openref_rt595_integrated_update_begin(
    uint32_t session, uint8_t slot, const uint8_t manifest[OPENREF_UPDATE_MANIFEST_BYTES],
    uint32_t now_us)
{
    return update_ready ? openref_rt595_update_delivery_begin(&update_delivery,
        session, slot, manifest, now_us) : OPENREF_RT595_UPDATE_DELIVERY_REJECTED;
}

openref_rt595_update_delivery_result_t openref_rt595_integrated_update_chunk(
    uint32_t session, uint32_t sequence, uint32_t offset, const uint8_t *data,
    uint16_t length, uint32_t now_us)
{
    return update_ready ? openref_rt595_update_delivery_chunk(&update_delivery,
        session, sequence, offset, data, length, now_us) :
        OPENREF_RT595_UPDATE_DELIVERY_REJECTED;
}

openref_rt595_update_delivery_result_t openref_rt595_integrated_update_finish(
    uint32_t session, uint32_t sequence, uint32_t now_us)
{
    return update_ready ? openref_rt595_update_delivery_finish(&update_delivery,
        session, sequence, now_us) : OPENREF_RT595_UPDATE_DELIVERY_REJECTED;
}

void openref_rt595_integrated_update_reset(void)
{
    if (update_ready) openref_rt595_update_delivery_reset(&update_delivery);
}

__attribute__((weak)) bool openref_rt595_integrated_board_configure(
    openref_rt595_audio_io_mcux_config_t *io,
    openref_rt595_audio_spi_mcux_config_t *spi,
    uint8_t *local_source_id)
{
    (void)io;
    (void)spi;
    (void)local_source_id;
    return false;
}

/* Board port must synchronously control the codec's physical mute/shutdown. */
__attribute__((weak)) bool openref_rt595_integrated_board_set_output_muted(bool muted)
{
    (void)muted;
    return false;
}

static bool set_output_muted(void *context, bool muted)
{
    (void)context;
    return openref_rt595_integrated_board_set_output_muted(muted);
}

static void stop_audio(void *context)
{
    (void)context;
    openref_rt595_audio_io_stop(&audio_io.io);
}

static void abort_link(void *context)
{
    (void)context;
    openref_rt595_audio_spi_reset(&audio_spi.port);
}

static uint32_t clock_us(void *context)
{
    (void)context;
    return CTIMER_GetTimerCountValue(CTIMER0);
}

static bool timer_init(void)
{
    CLOCK_AttachClk(kMAIN_CLK_to_CTIMER0);
    uint32_t hz = CLOCK_GetCtimerClkFreq(0u);
    if (hz < 1000000u || hz % 1000000u != 0u) return false;
    ctimer_config_t config;
    CTIMER_GetDefaultConfig(&config);
    config.prescale = hz / 1000000u - 1u;
    CTIMER_Init(CTIMER0, &config);
    CTIMER_StartTimer(CTIMER0);
    return true;
}

int main(void)
{
    BOARD_InitHardware();
    openref_rt595_audio_io_mcux_config_t io_config = {0};
    openref_rt595_audio_spi_mcux_config_t spi_config = {0};
    uint8_t local_source_id = 0u;
    if (!timer_init() ||
        !openref_rt595_integrated_board_configure(
            &io_config, &spi_config, &local_source_id) ||
        local_source_id < 1u || local_source_id > 6u) {
        PRINTF("OPENREF_RT595_INTEGRATED board_port=missing\r\n");
        for (;;) __WFI();
    }
    const openref_rt595_output_guard_ops_t output_ops = {
        set_output_muted, stop_audio, abort_link, NULL
    };
    if (!openref_rt595_output_guard_init(&output_guard, &output_ops)) {
        PRINTF("OPENREF_RT595_INTEGRATED output_mute=fail\r\n");
        for (;;) __WFI();
    }
    if (io_config.dma != spi_config.dma_base) {
        PRINTF("OPENREF_RT595_INTEGRATED dma_topology=invalid\r\n");
        for (;;) __WFI();
    }
    DMA_Init(io_config.dma);
    if (!openref_rt595_lc3_init(&codec) ||
        !openref_audio_runtime_init(&runtime, local_source_id, 0u) ||
        !openref_rt595_audio_spi_mcux_init(&audio_spi, &spi_config) ||
        !openref_rt595_audio_io_mcux_init(&audio_io, &io_config) ||
        !openref_watchdog_gate_init(&watchdog_gate,
            &(openref_watchdog_gate_config_t){1u, 50u, {50u}},
            (uint64_t)clock_us(NULL) / 1000u) ||
        !openref_rt595_watchdog_init(250u)) {
        PRINTF("OPENREF_RT595_INTEGRATED init=fail\r\n");
        for (;;) __WFI();
    }
    if (!confirmation_storage_init()) {
        openref_rt595_output_guard_fault(&output_guard);
        PRINTF("OPENREF_RT595_INTEGRATED confirmation_state=invalid\r\n");
        for (;;) __WFI();
    }
    update_ready = update_delivery_init();
    PRINTF("OPENREF_RT595_INTEGRATED ready sample_rate=16000 block_samples=160\r\n");
    for (;;) {
        uint32_t now = clock_us(NULL);
        if (update_ready) (void)openref_rt595_update_delivery_poll(&update_delivery, now);
        openref_rt595_audio_spi_poll(&audio_spi.port, now);
        if (audio_io.io.dma_failures != 0u || audio_spi.port.start_failures != 0u ||
            audio_spi.port.transfer_errors != 0u || audio_spi.port.short_transfers != 0u) {
            openref_rt595_output_guard_fault(&output_guard);
            PRINTF("OPENREF_RT595_INTEGRATED output=fault\r\n");
            for (;;) __WFI();
        }
        if (!openref_rt595_output_guard_set_ready(&output_guard, true,
                audio_spi.port.transport.latest_status_valid,
                watchdog_ready && watchdog_gate.last_fault_mask == 0u)) {
            PRINTF("OPENREF_RT595_INTEGRATED output_gate=fail\r\n");
            for (;;) __WFI();
        }
        openref_audio_link_frame_t remote;
        while (openref_rt595_audio_spi_pop_audio(&audio_spi.port, &remote))
            (void)openref_audio_runtime_ingest_remote(&runtime, &remote);
        int16_t microphone[OPENREF_AUDIO_FRAME_SAMPLES];
        int16_t headphone[OPENREF_AUDIO_FRAME_SAMPLES];
        if (openref_rt595_audio_io_take_capture(&audio_io.io, microphone)) {
            if (openref_audio_runtime_process(&runtime, microphone, now,
                    openref_rt595_lc3_encode, openref_rt595_lc3_decode,
                    clock_us, &codec, NULL, headphone)) {
                openref_audio_link_frame_t local;
                if (openref_audio_runtime_take_local(&runtime, &local))
                    (void)openref_rt595_audio_spi_queue(&audio_spi.port, &local);
                (void)openref_rt595_audio_io_submit_playout(&audio_io.io, headphone);
                uint64_t now_ms = (uint64_t)clock_us(NULL) / 1000u;
                (void)openref_watchdog_gate_should_feed(&watchdog_gate, now_ms);
                if (watchdog_gate.last_fault_mask == 0u &&
                    openref_watchdog_gate_report(&watchdog_gate, 0u, now_ms) &&
                    openref_watchdog_gate_should_feed(&watchdog_gate, now_ms)) {
                    openref_rt595_watchdog_feed();
                    watchdog_ready = true;
                }
                if (confirmation_active) {
                    const openref_rt595_app_health_t health = {
                        .clocks_ok = CLOCK_GetCtimerClkFreq(0u) >= 1000000u,
                        .storage_ok = confirmation_boot_state.store.loaded,
                        .watchdog_ok = watchdog_ready && watchdog_gate.last_fault_mask == 0u,
                        .audio_ok = !output_guard.fault_latched && audio_io.io.dma_failures == 0u,
                        .peer_ok = audio_spi.port.transport.latest_status_valid,
                        .fault_free = audio_spi.port.transfer_errors == 0u &&
                            audio_spi.port.short_transfers == 0u,
                    };
                    if (openref_rt595_app_confirmation_observe(&confirmation, health,
                            (uint32_t)now_ms)) confirmation_active = false;
                }
            } else {
                openref_rt595_app_confirmation_fault(&confirmation);
                openref_rt595_output_guard_fault(&output_guard);
                PRINTF("OPENREF_RT595_INTEGRATED runtime=fault\r\n");
                for (;;) __WFI();
            }
        }
    }
}
