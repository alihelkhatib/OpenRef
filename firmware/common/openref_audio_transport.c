#include "openref_audio_transport.h"

#include <stddef.h>
#include <string.h>

void openref_audio_transport_init(openref_audio_transport_t *transport)
{
    if (transport == NULL) {
        return;
    }
    memset(transport, 0, sizeof(*transport));
    openref_audio_link_queue_init(&transport->audio_tx);
    openref_audio_link_queue_init(&transport->audio_rx);
}

bool openref_audio_transport_queue(
    openref_audio_transport_t *transport,
    const openref_audio_link_frame_t *frame)
{
    if (transport == NULL || frame == NULL) {
        return false;
    }
    uint8_t validation_wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    if (!openref_audio_link_encode(frame, validation_wire, sizeof(validation_wire))) {
        return false;
    }
    if (frame->kind == OPENREF_AUDIO_LINK_STATUS) {
        transport->pending_status = *frame;
        transport->status_pending = true;
        return true;
    }
    return openref_audio_link_queue_push(&transport->audio_tx, frame);
}

bool openref_audio_transport_request_asserted(
    const openref_audio_transport_t *transport)
{
    return transport != NULL &&
        (transport->audio_tx.count != 0u || transport->status_pending);
}

bool openref_audio_transport_prepare_tx(
    openref_audio_transport_t *transport,
    uint32_t timestamp_us,
    uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES])
{
    if (transport == NULL || wire == NULL) {
        return false;
    }

    openref_audio_link_frame_t frame;
    if (!openref_audio_link_queue_pop(&transport->audio_tx, &frame)) {
        if (transport->status_pending) {
            frame = transport->pending_status;
            transport->status_pending = false;
        } else {
            memset(&frame, 0, sizeof(frame));
            frame.kind = OPENREF_AUDIO_LINK_STATUS;
            frame.sequence = transport->idle_sequence++;
            frame.timestamp_us = timestamp_us;
            transport->idle_transactions++;
        }
    }
    frame.producer_queue_depth = transport->audio_tx.count;
    if (!openref_audio_link_encode(&frame, wire, OPENREF_AUDIO_LINK_FRAME_BYTES)) {
        return false;
    }
    transport->transactions++;
    return true;
}

bool openref_audio_transport_accept_rx(
    openref_audio_transport_t *transport,
    const uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES])
{
    if (transport == NULL || wire == NULL) {
        return false;
    }
    openref_audio_link_frame_t frame;
    if (!openref_audio_link_decode(wire, OPENREF_AUDIO_LINK_FRAME_BYTES, &frame)) {
        transport->malformed_frames++;
        return false;
    }
    if (frame.kind == OPENREF_AUDIO_LINK_STATUS) {
        transport->latest_status = frame;
        transport->latest_status_valid = true;
        transport->status_received++;
        return true;
    }

    uint8_t source_index = (uint8_t)(frame.source_id - 1u);
    if (transport->sequence_valid[source_index] &&
        frame.sequence != (uint16_t)(transport->last_sequence[source_index] + 1u)) {
        transport->sequence_gaps++;
        frame.flags |= OPENREF_AUDIO_LINK_FLAG_DISCONTINUITY;
    }
    transport->last_sequence[source_index] = frame.sequence;
    transport->sequence_valid[source_index] = true;
    return openref_audio_link_queue_push(&transport->audio_rx, &frame);
}

bool openref_audio_transport_pop_audio(
    openref_audio_transport_t *transport,
    openref_audio_link_frame_t *frame)
{
    if (transport == NULL) {
        return false;
    }
    return openref_audio_link_queue_pop(&transport->audio_rx, frame);
}
