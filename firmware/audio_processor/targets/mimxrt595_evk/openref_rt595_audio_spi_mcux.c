#include "openref_rt595_audio_spi_mcux.h"

#include <stddef.h>
#include <string.h>

static void dma_complete(SPI_Type *base, spi_dma_handle_t *handle, status_t status, void *user_data)
{
    openref_rt595_audio_spi_mcux_t *adapter = user_data;
    size_t bytes = 0u;
    (void)base;
    (void)handle;
    if (status == kStatus_Success) {
        bytes = OPENREF_AUDIO_LINK_FRAME_BYTES;
    } else {
        (void)SPI_SlaveTransferGetCountDMA(adapter->config.spi_base, &adapter->spi_dma, &bytes);
    }
    if (bytes > UINT16_MAX) {
        bytes = 0u;
    }
    openref_rt595_audio_spi_complete(&adapter->port, status == kStatus_Success, (uint16_t)bytes);
}

static bool start_transfer(void *context, const uint8_t *tx, uint8_t *rx, uint16_t bytes)
{
    openref_rt595_audio_spi_mcux_t *adapter = context;
    spi_transfer_t transfer = {0};
    transfer.txData = (uint8_t *)(uintptr_t)tx;
    transfer.rxData = rx;
    transfer.dataSize = bytes;
    transfer.configFlags = kSPI_FrameAssert;
    return SPI_SlaveTransferDMA(adapter->config.spi_base, &adapter->spi_dma, &transfer) == kStatus_Success;
}

static void abort_transfer(void *context)
{
    openref_rt595_audio_spi_mcux_t *adapter = context;
    SPI_SlaveTransferAbortDMA(adapter->config.spi_base, &adapter->spi_dma);
}

static void set_request(void *context, bool asserted)
{
    openref_rt595_audio_spi_mcux_t *adapter = context;
    adapter->config.set_request(adapter->config.request_context, asserted);
}

bool openref_rt595_audio_spi_mcux_init(openref_rt595_audio_spi_mcux_t *adapter,
                                      const openref_rt595_audio_spi_mcux_config_t *config)
{
    spi_slave_config_t slave_config;
    openref_rt595_audio_spi_ops_t ops;
    if ((adapter == NULL) || (config == NULL) || (config->spi_base == NULL) ||
        (config->dma_base == NULL) || (config->set_request == NULL) ||
        (config->rx_dma_channel == config->tx_dma_channel)) {
        return false;
    }
    memset(adapter, 0, sizeof(*adapter));
    adapter->config = *config;
    SPI_SlaveGetDefaultConfig(&slave_config);
    slave_config.sselPol = kSPI_SpolActiveAllLow;
    if (SPI_SlaveInit(config->spi_base, &slave_config) != kStatus_Success) {
        return false;
    }
    DMA_EnableChannel(config->dma_base, config->tx_dma_channel);
    DMA_EnableChannel(config->dma_base, config->rx_dma_channel);
    DMA_SetChannelPriority(config->dma_base, config->tx_dma_channel, kDMA_ChannelPriority0);
    DMA_SetChannelPriority(config->dma_base, config->rx_dma_channel, kDMA_ChannelPriority1);
    DMA_CreateHandle(&adapter->tx_dma, config->dma_base, config->tx_dma_channel);
    DMA_CreateHandle(&adapter->rx_dma, config->dma_base, config->rx_dma_channel);
    if (SPI_SlaveTransferCreateHandleDMA(config->spi_base, &adapter->spi_dma, dma_complete,
                                         adapter, &adapter->tx_dma, &adapter->rx_dma) != kStatus_Success) {
        SPI_Deinit(config->spi_base);
        return false;
    }
    ops.start = start_transfer;
    ops.abort = abort_transfer;
    ops.set_request = set_request;
    ops.context = adapter;
    return openref_rt595_audio_spi_init(&adapter->port, &ops);
}
