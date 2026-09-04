#ifndef OPENREF_RT595_AUDIO_SPI_H
#define OPENREF_RT595_AUDIO_SPI_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_transport.h"

typedef bool (*openref_rt595_spi_start_fn)(void *context, const uint8_t *tx, uint8_t *rx, uint16_t bytes);
typedef void (*openref_rt595_spi_abort_fn)(void *context);
typedef void (*openref_rt595_spi_request_fn)(void *context, bool asserted);

typedef struct {
    openref_rt595_spi_start_fn start;
    openref_rt595_spi_abort_fn abort;
    openref_rt595_spi_request_fn set_request;
    void *context;
} openref_rt595_audio_spi_ops_t;

typedef struct {
    openref_audio_transport_t transport;
    openref_rt595_audio_spi_ops_t ops;
    uint8_t tx[OPENREF_AUDIO_LINK_FRAME_BYTES];
    uint8_t rx[OPENREF_AUDIO_LINK_FRAME_BYTES];
    volatile uint16_t completion_bytes;
    volatile bool completion_pending;
    volatile bool completion_success;
    volatile bool transfer_active;
    bool transfer_requested;
    bool initialized;
    uint32_t transfers_started;
    uint32_t transfers_completed;
    uint32_t start_failures;
    uint32_t transfer_errors;
    uint32_t short_transfers;
    uint32_t duplicate_completions;
    uint32_t resets;
} openref_rt595_audio_spi_t;

bool openref_rt595_audio_spi_init(openref_rt595_audio_spi_t *spi, const openref_rt595_audio_spi_ops_t *ops);
bool openref_rt595_audio_spi_queue(openref_rt595_audio_spi_t *spi, const openref_audio_link_frame_t *frame);
void openref_rt595_audio_spi_poll(openref_rt595_audio_spi_t *spi, uint32_t timestamp_us);
void openref_rt595_audio_spi_complete(openref_rt595_audio_spi_t *spi, bool success, uint16_t bytes);
bool openref_rt595_audio_spi_pop_audio(openref_rt595_audio_spi_t *spi, openref_audio_link_frame_t *frame);
void openref_rt595_audio_spi_reset(openref_rt595_audio_spi_t *spi);

#endif
