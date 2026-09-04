#include "openref_rt595_audio_spi.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static void increment(uint32_t *value)
{
    if (*value != UINT32_MAX) {
        ++*value;
    }
}

static void update_request(openref_rt595_audio_spi_t *spi)
{
    const bool asserted = (spi->transfer_active && spi->transfer_requested) ||
                          openref_audio_transport_request_asserted(&spi->transport);
    spi->ops.set_request(spi->ops.context, asserted);
}

static void arm(openref_rt595_audio_spi_t *spi, uint32_t timestamp_us)
{
    if (spi->transfer_active) {
        return;
    }
    spi->transfer_requested = openref_audio_transport_request_asserted(&spi->transport);
    if (!openref_audio_transport_prepare_tx(&spi->transport, timestamp_us, spi->tx) ||
        !spi->ops.start(spi->ops.context, spi->tx, spi->rx, OPENREF_AUDIO_LINK_FRAME_BYTES)) {
        spi->transfer_requested = false;
        increment(&spi->start_failures);
        update_request(spi);
        return;
    }
    spi->transfer_active = true;
    increment(&spi->transfers_started);
    update_request(spi);
}

bool openref_rt595_audio_spi_init(openref_rt595_audio_spi_t *spi, const openref_rt595_audio_spi_ops_t *ops)
{
    if ((spi == NULL) || (ops == NULL) || (ops->start == NULL) ||
        (ops->abort == NULL) || (ops->set_request == NULL)) {
        return false;
    }
    memset(spi, 0, sizeof(*spi));
    spi->ops = *ops;
    openref_audio_transport_init(&spi->transport);
    spi->initialized = true;
    spi->ops.set_request(spi->ops.context, false);
    return true;
}

bool openref_rt595_audio_spi_queue(openref_rt595_audio_spi_t *spi, const openref_audio_link_frame_t *frame)
{
    if ((spi == NULL) || !spi->initialized || !openref_audio_transport_queue(&spi->transport, frame)) {
        return false;
    }
    update_request(spi);
    return true;
}

void openref_rt595_audio_spi_complete(openref_rt595_audio_spi_t *spi, bool success, uint16_t bytes)
{
    if ((spi == NULL) || !spi->initialized || !spi->transfer_active || spi->completion_pending) {
        if ((spi != NULL) && spi->initialized) {
            increment(&spi->duplicate_completions);
        }
        return;
    }
    spi->completion_success = success;
    spi->completion_bytes = bytes;
    spi->completion_pending = true;
}

void openref_rt595_audio_spi_poll(openref_rt595_audio_spi_t *spi, uint32_t timestamp_us)
{
    if ((spi == NULL) || !spi->initialized) {
        return;
    }
    if (spi->completion_pending) {
        const bool success = spi->completion_success;
        const uint16_t bytes = spi->completion_bytes;
        spi->completion_pending = false;
        spi->transfer_active = false;
        spi->transfer_requested = false;
        increment(&spi->transfers_completed);
        if (!success) {
            increment(&spi->transfer_errors);
        } else if (bytes != OPENREF_AUDIO_LINK_FRAME_BYTES) {
            increment(&spi->short_transfers);
        } else {
            (void)openref_audio_transport_accept_rx(&spi->transport, spi->rx);
        }
    }
    update_request(spi);
    arm(spi, timestamp_us);
}

bool openref_rt595_audio_spi_pop_audio(openref_rt595_audio_spi_t *spi, openref_audio_link_frame_t *frame)
{
    return (spi != NULL) && spi->initialized && openref_audio_transport_pop_audio(&spi->transport, frame);
}

void openref_rt595_audio_spi_reset(openref_rt595_audio_spi_t *spi)
{
    if ((spi == NULL) || !spi->initialized) {
        return;
    }
    if (spi->transfer_active) {
        spi->ops.abort(spi->ops.context);
    }
    openref_audio_transport_init(&spi->transport);
    memset(spi->tx, 0, sizeof(spi->tx));
    memset(spi->rx, 0, sizeof(spi->rx));
    spi->completion_pending = false;
    spi->transfer_active = false;
    spi->transfer_requested = false;
    increment(&spi->resets);
    spi->ops.set_request(spi->ops.context, false);
}
