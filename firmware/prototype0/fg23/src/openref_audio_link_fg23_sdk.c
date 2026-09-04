#include "openref_audio_link_fg23_sdk.h"
#include <stddef.h>
#include "em_cmu.h"
#include "em_eusart.h"
#include "em_gpio.h"
#include "rail.h"
#include "sl_device_dma.h"
#include "sl_dma_channel.h"
#include "sl_dma_manager.h"
#include "sl_status.h"

#define AUDIO_EUSART EUSART1
#define AUDIO_COPI_PORT gpioPortA
#define AUDIO_COPI_PIN 7u
#define AUDIO_CIPO_PORT gpioPortA
#define AUDIO_CIPO_PIN 8u
#define AUDIO_SCLK_PORT gpioPortB
#define AUDIO_SCLK_PIN 0u
#define AUDIO_CS_PORT gpioPortB
#define AUDIO_CS_PIN 1u
#define AUDIO_REQ_PORT gpioPortB
#define AUDIO_REQ_PIN 2u
#define AUDIO_RESET_PORT gpioPortB
#define AUDIO_RESET_PIN 3u

typedef struct {
    openref_audio_fg23_t *adapter;
    sl_dma_channel_handle_t rx, tx;
    sl_dma_channel_xfer_descriptor_t *rx_desc, *tx_desc;
    uint8_t rx_number, tx_number;
    volatile bool rx_done, tx_done, error;
    bool active;
} audio_sdk_t;
static audio_sdk_t sdk;

static void dma_done(sl_dma_channel_handle_t *handle, void *arg, bool error, bool aborted)
{
    audio_sdk_t *s = (audio_sdk_t *)arg;
    if (s == NULL || !s->active) return;
    s->error = s->error || error || aborted;
    if (handle == &s->rx) s->rx_done = true;
    else if (handle == &s->tx) s->tx_done = true;
    else s->error = true;
}

static bool abort_transfer(void *arg)
{
    audio_sdk_t *s = (audio_sdk_t *)arg;
    if (s == NULL) return false;
    s->active = false;
    bool ok = sl_dma_channel_abort(&s->rx) == SL_STATUS_OK;
    ok = sl_dma_channel_abort(&s->tx) == SL_STATUS_OK && ok;
    GPIO_PinOutSet(AUDIO_CS_PORT, AUDIO_CS_PIN);
    s->rx_done = s->tx_done = s->error = false;
    return ok;
}

static bool start_transfer(void *arg, const uint8_t *tx, uint8_t *rx, uint16_t length)
{
    audio_sdk_t *s = (audio_sdk_t *)arg;
    if (s == NULL || tx == NULL || rx == NULL || s->active ||
        length != OPENREF_AUDIO_LINK_FRAME_BYTES) return false;
    s->rx_done = s->tx_done = s->error = false;
    s->active = true;
    EUSART_IntClear(AUDIO_EUSART, _EUSART_IF_MASK);
    GPIO_PinOutClear(AUDIO_CS_PORT, AUDIO_CS_PIN);
    if (sl_dma_channel_submit_transfer_p2m(&s->rx, (void *)&AUDIO_EUSART->RXDATA,
            rx, length, SL_DMA_CTRL_SIZE_BYTE, s->rx_desc) != SL_STATUS_OK ||
        sl_dma_channel_submit_transfer_m2p(&s->tx, (void *)tx,
            (void *)&AUDIO_EUSART->TXDATA, length, SL_DMA_CTRL_SIZE_BYTE,
            s->tx_desc) != SL_STATUS_OK) {
        (void)abort_transfer(s);
        return false;
    }
    return true;
}

static bool request_asserted(void *arg) { (void)arg; return GPIO_PinInGet(AUDIO_REQ_PORT, AUDIO_REQ_PIN) == 0; }
static bool set_reset(void *arg, bool asserted) { (void)arg; if (asserted) GPIO_PinOutClear(AUDIO_RESET_PORT, AUDIO_RESET_PIN); else GPIO_PinOutSet(AUDIO_RESET_PORT, AUDIO_RESET_PIN); return true; }
static uint32_t clock_us(void *arg) { (void)arg; return RAIL_GetTime(); }

bool openref_audio_fg23_sdk_init(openref_audio_fg23_t *adapter)
{
    EUSART_SpiInit_TypeDef spi = EUSART_SPI_MASTER_INIT_DEFAULT_HF;
    const openref_audio_fg23_config_t config = { .reset_hold_us = 10000u, .transfer_timeout_us = 2000u };
    const openref_audio_fg23_hooks_t hooks = { start_transfer, abort_transfer, request_asserted, set_reset, clock_us, &sdk };
    if (adapter == NULL) return false;
    sdk.adapter = adapter;
    GPIO_PinModeSet(AUDIO_RESET_PORT, AUDIO_RESET_PIN, gpioModePushPull, 0);
    GPIO_PinModeSet(AUDIO_CS_PORT, AUDIO_CS_PIN, gpioModePushPull, 1);
    GPIO_PinModeSet(AUDIO_REQ_PORT, AUDIO_REQ_PIN, gpioModeInputPullFilter, 1);
    GPIO_PinModeSet(AUDIO_COPI_PORT, AUDIO_COPI_PIN, gpioModePushPull, 0);
    GPIO_PinModeSet(AUDIO_CIPO_PORT, AUDIO_CIPO_PIN, gpioModeInput, 0);
    GPIO_PinModeSet(AUDIO_SCLK_PORT, AUDIO_SCLK_PIN, gpioModePushPull, 0);
    CMU_ClockEnable(cmuClock_EUSART1, true);
    GPIO->EUSARTROUTE[EUSART_NUM(AUDIO_EUSART)].TXROUTE = (AUDIO_COPI_PORT << _GPIO_EUSART_TXROUTE_PORT_SHIFT) | (AUDIO_COPI_PIN << _GPIO_EUSART_TXROUTE_PIN_SHIFT);
    GPIO->EUSARTROUTE[EUSART_NUM(AUDIO_EUSART)].RXROUTE = (AUDIO_CIPO_PORT << _GPIO_EUSART_RXROUTE_PORT_SHIFT) | (AUDIO_CIPO_PIN << _GPIO_EUSART_RXROUTE_PIN_SHIFT);
    GPIO->EUSARTROUTE[EUSART_NUM(AUDIO_EUSART)].SCLKROUTE = (AUDIO_SCLK_PORT << _GPIO_EUSART_SCLKROUTE_PORT_SHIFT) | (AUDIO_SCLK_PIN << _GPIO_EUSART_SCLKROUTE_PIN_SHIFT);
    GPIO->EUSARTROUTE[EUSART_NUM(AUDIO_EUSART)].ROUTEEN = GPIO_EUSART_ROUTEEN_TXPEN | GPIO_EUSART_ROUTEEN_RXPEN | GPIO_EUSART_ROUTEEN_SCLKPEN;
    spi.bitRate = 8000000u;
    spi.clockMode = eusartClockMode0;
    EUSART_SpiInit(AUDIO_EUSART, &spi);
    if (sl_dma_manager_allocate_channel(NULL, &sdk.rx_number) != SL_STATUS_OK ||
        sl_dma_manager_allocate_channel(NULL, &sdk.tx_number) != SL_STATUS_OK ||
        sl_dma_channel_init(&sdk.rx, NULL, sdk.rx_number, dma_done, &sdk) != SL_STATUS_OK ||
        sl_dma_channel_init(&sdk.tx, NULL, sdk.tx_number, dma_done, &sdk) != SL_STATUS_OK ||
        sl_dma_channel_set_peripheral_signal(&sdk.rx, SL_DMA_SIGNAL_EUSART1_RXFL) != SL_STATUS_OK ||
        sl_dma_channel_set_peripheral_signal(&sdk.tx, SL_DMA_SIGNAL_EUSART1_TXFL) != SL_STATUS_OK ||
        sl_dma_channel_descriptor_alloc(&sdk.rx, &sdk.rx_desc) != SL_STATUS_OK ||
        sl_dma_channel_descriptor_alloc(&sdk.tx, &sdk.tx_desc) != SL_STATUS_OK) return false;
    return openref_audio_fg23_init(adapter, &config, hooks);
}

void openref_audio_fg23_sdk_process(void)
{
    if (sdk.active && sdk.error) {
        (void)abort_transfer(&sdk);
        (void)openref_audio_fg23_transfer_complete_isr(sdk.adapter, false);
    } else if (sdk.active && sdk.rx_done && sdk.tx_done &&
        (AUDIO_EUSART->STATUS & EUSART_STATUS_TXC) != 0u) {
        sdk.active = false;
        GPIO_PinOutSet(AUDIO_CS_PORT, AUDIO_CS_PIN);
        (void)openref_audio_fg23_transfer_complete_isr(sdk.adapter, true);
    }
    if (sdk.adapter != NULL) (void)openref_audio_fg23_process(sdk.adapter);
}
