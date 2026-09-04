#include <stdbool.h>
#include <stdint.h>

#include "board.h"
#include "flash_config.h"
#include "fsl_common.h"
#include "openref_rt595_boot_coordinator.h"
#include "openref_rt595_boot_handoff_mcux.h"
#include "openref_rt595_boot_state_mcux.h"
#include "openref_rt595_bootstrap.h"
#include "openref_rt595_slot_authenticator_mcux.h"
#include "openref_rt595_update_crypto_mcux.h"

#define OPENREF_FLASH_END       0x08200000u
#define OPENREF_SLOT_A_MANIFEST 0x08040000u
#define OPENREF_SLOT_A_IMAGE    0x08041000u
#define OPENREF_SLOT_B_MANIFEST 0x08100000u
#define OPENREF_SLOT_B_IMAGE    0x08101000u
#define OPENREF_SLOT_CAPACITY   0x000bf000u
#define OPENREF_BOOT_STATE_BASE 0x081fe000u
#define OPENREF_RT595_RAM_BASE  0x20280000u
#define OPENREF_RT595_RAM_BYTES 0x00280000u
#define OPENREF_HARDWARE_ID     0x59500001u
#define OPENREF_BOOTLOADER_VER  1u
#define OPENREF_TRIAL_ATTEMPTS  3u

extern const flexspi_nor_config_t flash_config;

static openref_rt595_update_crypto_mcux_t crypto;
static openref_rt595_slot_authenticator_mcux_t authenticator;
static openref_rt595_boot_state_mcux_t boot_state;
static openref_rt595_boot_coordinator_t coordinator;

#define OPENREF_RECOVERY_STATUS_MAGIC 0x4f520000u /* "OR" + reason */

static void status(void *context,
    openref_rt595_bootstrap_recovery_reason_t reason)
{
    uint32_t count;
    (void)context;
    /* RTC GPREG survives a watchdog reset and is debugger/service-tool
     * readable.  It is status only: it grants no write or boot authority. */
    RTC->GPREG[0] = OPENREF_RECOVERY_STATUS_MAGIC | (uint32_t)reason;
    count = RTC->GPREG[1];
    if (count != UINT32_MAX) RTC->GPREG[1] = count + 1u;
    __DSB();
}

static bool prepare(void *context,
    const openref_rt595_boot_handoff_layout_t *layout,
    openref_rt595_boot_handoff_plan_t *plan)
{
    (void)context;
    return openref_rt595_boot_handoff_mcux_prepare(layout, plan);
}

static void transfer(void *context, const openref_rt595_boot_handoff_plan_t *plan)
{
    (void)context;
    openref_rt595_boot_handoff_mcux_execute(plan);
}

static void recovery(void *context)
{
    (void)context;
    __disable_irq();
    SysTick->CTRL = 0u;
    for (;;) {
        __DSB();
        __WFI();
    }
}

int main(void)
{
    flexspi_nor_config_t *config = (flexspi_nor_config_t *)(uintptr_t)&flash_config;
    const openref_update_platform_t platform = {
        .target = OPENREF_UPDATE_TARGET_AUDIO,
        .hardware_id = OPENREF_HARDWARE_ID,
        .bootloader_version = OPENREF_BOOTLOADER_VER,
        .antirollback_floor = 0u,
        .confirmed_image_version = 0u,
        .maximum_image_bytes = OPENREF_SLOT_CAPACITY,
    };
    openref_rt595_bootstrap_t bootstrap;

    BOARD_InitBootClocks();
    if (!openref_rt595_update_crypto_mcux_init(&crypto,
            openref_trust_anchor_key_id, openref_trust_anchor_public_key) ||
        !openref_rt595_slot_authenticator_mcux_init(&authenticator, 0u, config,
            &platform, openref_rt595_update_crypto_callbacks(&crypto.crypto),
            OPENREF_SLOT_A_MANIFEST, OPENREF_SLOT_A_IMAGE, OPENREF_SLOT_CAPACITY,
            OPENREF_SLOT_B_MANIFEST, OPENREF_SLOT_B_IMAGE, OPENREF_SLOT_CAPACITY) ||
        !openref_rt595_boot_state_mcux_init(&boot_state, config, 0u,
            OPENREF_BOOT_STATE_BASE, OPENREF_BOOT_STATE_BASE, OPENREF_FLASH_END) ||
        !openref_rt595_boot_coordinator_init(&coordinator,
            &authenticator.authenticator, &boot_state.store, OPENREF_TRIAL_ATTEMPTS)) {
        status(NULL, OPENREF_RT595_BOOTSTRAP_RECOVERY_CONFIGURATION);
        recovery(NULL);
    }
    /* A missing/corrupt state record is deliberately not reconstructed from
     * images: doing so would erase the durable anti-rollback floor.  The
     * bootstrap runner reports the distinct state failure and stays closed. */
    (void)openref_rt595_boot_state_load(&boot_state.store);
    bootstrap = (openref_rt595_bootstrap_t){
        .coordinator = &coordinator,
        .image_base = {OPENREF_SLOT_A_IMAGE, OPENREF_SLOT_B_IMAGE},
        .image_capacity = {OPENREF_SLOT_CAPACITY, OPENREF_SLOT_CAPACITY},
        .ram_base = OPENREF_RT595_RAM_BASE,
        .ram_size = OPENREF_RT595_RAM_BYTES,
        .vtor_alignment = OPENREF_RT595_BOOT_MIN_VTOR_ALIGNMENT,
        .prepare = prepare,
        .transfer = transfer,
        .recovery = recovery,
        .status = status,
        .context = NULL,
    };
    (void)openref_rt595_bootstrap_run(&bootstrap);
    recovery(NULL);
}
