#include <stdbool.h>
#include <stdint.h>
#include "board.h"
#include "fsl_clock.h"
#include "fsl_codec_common.h"
#include "fsl_dmic.h"
#include "fsl_gpio.h"
#include "fsl_i2s.h"
#include "fsl_inputmux.h"
#include "fsl_iopctl.h"
#include "pin_mux.h"
#include "openref_rt595_audio_io_mcux.h"
#include "openref_rt595_audio_spi_mcux.h"
#include "openref_rt595_board_resources.h"

#if !defined(OPENREF_LOCAL_SOURCE_ID) || OPENREF_LOCAL_SOURCE_ID < 1 || OPENREF_LOCAL_SOURCE_ID > 6
#error "OPENREF_LOCAL_SOURCE_ID must be 1..6"
#endif

#define OPENREF_CODEC_CHANNELS (kCODEC_PlayChannelHeadphoneLeft | kCODEC_PlayChannelHeadphoneRight)

extern codec_config_t boardCodecConfig;
extern wm8904_config_t wm8904Config;
static codec_handle_t codec_handle;
static bool codec_ready;

static void set_request(void *context, bool asserted)
{
    (void)context;
    GPIO_PinWrite(GPIO, OPENREF_RT595_AUDIO_REQUEST_PORT, OPENREF_RT595_AUDIO_REQUEST_PIN,
                  asserted ? 0u : 1u);
}

bool openref_rt595_integrated_board_set_output_muted(bool muted)
{
    return codec_ready && CODEC_SetMute(&codec_handle, OPENREF_CODEC_CHANNELS, muted) == kStatus_Success;
}

static void configure_spi_and_request_pins(void)
{
    const uint32_t spi_pin = IOPCTL_PIO_FUNC1 | IOPCTL_PIO_PUPD_DI | IOPCTL_PIO_PULLDOWN_EN |
        IOPCTL_PIO_INBUF_EN | IOPCTL_PIO_SLEW_RATE_NORMAL | IOPCTL_PIO_FULLDRIVE_DI |
        IOPCTL_PIO_ANAMUX_DI | IOPCTL_PIO_PSEDRAIN_DI | IOPCTL_PIO_INV_DI;
    IOPCTL_PinMuxSet(IOPCTL, 1u, 3u, spi_pin); /* JP26.4 FC5 SCK */
    IOPCTL_PinMuxSet(IOPCTL, 1u, 4u, spi_pin); /* JP26.3 FC5 MISO */
    IOPCTL_PinMuxSet(IOPCTL, 1u, 5u, spi_pin); /* JP26.2 FC5 MOSI */
    IOPCTL_PinMuxSet(IOPCTL, 1u, 6u, spi_pin); /* JP26.1 FC5 SSEL0 */
    IOPCTL_PinMuxSet(IOPCTL, OPENREF_RT595_AUDIO_REQUEST_PORT, OPENREF_RT595_AUDIO_REQUEST_PIN,
        IOPCTL_PIO_FUNC0 | IOPCTL_PIO_PUPD_DI | IOPCTL_PIO_INBUF_DI |
        IOPCTL_PIO_SLEW_RATE_NORMAL | IOPCTL_PIO_FULLDRIVE_DI | IOPCTL_PIO_ANAMUX_DI);
    GPIO_PortInit(GPIO, OPENREF_RT595_AUDIO_REQUEST_PORT);
    gpio_pin_config_t request = {kGPIO_DigitalOutput, 1u};
    GPIO_PinInit(GPIO, OPENREF_RT595_AUDIO_REQUEST_PORT, OPENREF_RT595_AUDIO_REQUEST_PIN, &request);
}

bool openref_rt595_integrated_board_configure(openref_rt595_audio_io_mcux_config_t *io,
    openref_rt595_audio_spi_mcux_config_t *spi, uint8_t *local_source_id)
{
    if (io == NULL || spi == NULL || local_source_id == NULL) return false;

    wm8904Config.format.sampleRate = kWM8904_SampleRate16kHz;
    if (CODEC_Init(&codec_handle, &boardCodecConfig) != kStatus_Success ||
        CODEC_SetVolume(&codec_handle, OPENREF_CODEC_CHANNELS, 20u) != kStatus_Success ||
        CODEC_SetMute(&codec_handle, OPENREF_CODEC_CHANNELS, true) != kStatus_Success) return false;
    codec_ready = true;

    dmic_channel_config_t dmic = {0};
    dmic.divhfclk = kDMIC_PdmDiv1;
    CLOCK_SetClkDiv(kCLOCK_DivDmicClk, 24u);
    dmic.osr = 32u; /* 24.576 MHz / 24 / (2 * 16 kHz). */
    dmic.gainshft = 3u;
    dmic.preac2coef = kDMIC_CompValueZero;
    dmic.preac4coef = kDMIC_CompValueZero;
    dmic.dc_cut_level = kDMIC_DcCut155;
    dmic.post_dc_gain_reduce = 1u;
    dmic.saturate16bit = 1u;
    dmic.sample_rate = kDMIC_PhyFullSpeed;
#if defined(FSL_FEATURE_DMIC_CHANNEL_HAS_SIGNEXTEND) && FSL_FEATURE_DMIC_CHANNEL_HAS_SIGNEXTEND
    dmic.enableSignExtend = true;
#endif
    DMIC_Init(DMIC0);
#if !(defined(FSL_FEATURE_DMIC_HAS_NO_IOCFG) && FSL_FEATURE_DMIC_HAS_NO_IOCFG)
    DMIC_SetIOCFG(DMIC0, kDMIC_PdmDual);
#endif
    DMIC_Use2fs(DMIC0, true);
    DMIC_ConfigChannel(DMIC0, kDMIC_Channel0, kDMIC_Left, &dmic);
    DMIC_FifoChannel(DMIC0, kDMIC_Channel0, 0u, false, true);
    DMIC_EnableChannnel(DMIC0, DMIC_CHANEN_EN_CH0(1));

    i2s_config_t i2s;
    I2S_TxGetDefaultConfig(&i2s);
    i2s.divider = 48u; /* 24.576 MHz / (16 kHz * 16 bits * 2 channels). */
    i2s.pdmData = false;
    i2s.masterSlave = kI2S_MasterSlaveNormalSlave;
    CLOCK_AttachClk(kAUDIO_PLL_to_FLEXCOMM3);
    I2S_TxInit(I2S3, &i2s);
    I2S_Enable(I2S3);

    configure_spi_and_request_pins();
    RESET_PeripheralReset(kINPUTMUX_RST_SHIFT_RSTn);
    INPUTMUX_Init(INPUTMUX);
    CLOCK_AttachClk(kFRO_DIV4_to_FLEXCOMM5);
    INPUTMUX_EnableSignal(INPUTMUX, kINPUTMUX_Flexcomm3TxToDmac0Ch7RequestEna, true);
    INPUTMUX_EnableSignal(INPUTMUX, kINPUTMUX_Dmic0Ch0ToDmac0Ch16RequestEna, true);
    INPUTMUX_EnableSignal(INPUTMUX, kINPUTMUX_Flexcomm5RxToDmac0Ch10RequestEna, true);
    INPUTMUX_EnableSignal(INPUTMUX, kINPUTMUX_Flexcomm5TxToDmac0Ch11RequestEna, true);
    INPUTMUX_Deinit(INPUTMUX);

    *io = (openref_rt595_audio_io_mcux_config_t){DMIC0, I2S3, DMA0, 0u, 16u, 7u};
    *spi = (openref_rt595_audio_spi_mcux_config_t){SPI5, DMA0, 10u, 11u, set_request, NULL};
    *local_source_id = (uint8_t)OPENREF_LOCAL_SOURCE_ID;
    return true;
}
