#ifndef OPENREF_RT595_AUDIO_SPI_MCUX_H
#define OPENREF_RT595_AUDIO_SPI_MCUX_H

#include "fsl_dma.h"
#include "fsl_spi_dma.h"
#include "openref_rt595_audio_spi.h"

typedef struct {
    SPI_Type *spi_base;
    DMA_Type *dma_base;
    uint32_t rx_dma_channel;
    uint32_t tx_dma_channel;
    openref_rt595_spi_request_fn set_request;
    void *request_context;
} openref_rt595_audio_spi_mcux_config_t;

typedef struct {
    openref_rt595_audio_spi_t port;
    openref_rt595_audio_spi_mcux_config_t config;
    dma_handle_t tx_dma;
    dma_handle_t rx_dma;
    spi_dma_handle_t spi_dma;
} openref_rt595_audio_spi_mcux_t;

/* Pin mux, clocks, SSEL0 routing and the active-low AUDIO_REQn GPIO are board-owned. */
bool openref_rt595_audio_spi_mcux_init(openref_rt595_audio_spi_mcux_t *adapter,
                                      const openref_rt595_audio_spi_mcux_config_t *config);

#endif
