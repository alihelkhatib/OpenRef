#ifndef OPENREF_AUDIO_TRANSPORT_H
#define OPENREF_AUDIO_TRANSPORT_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_link.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    openref_audio_link_queue_t audio_tx;
    openref_audio_link_queue_t audio_rx;
    openref_audio_link_frame_t pending_status;
    openref_audio_link_frame_t latest_status;
    bool status_pending;
    bool latest_status_valid;
    bool sequence_valid[6];
    uint16_t last_sequence[6];
    uint16_t idle_sequence;
    uint32_t transactions;
    uint32_t idle_transactions;
    uint32_t malformed_frames;
    uint32_t sequence_gaps;
    uint32_t status_received;
} openref_audio_transport_t;

void openref_audio_transport_init(openref_audio_transport_t *transport);

bool openref_audio_transport_queue(
    openref_audio_transport_t *transport,
    const openref_audio_link_frame_t *frame);

bool openref_audio_transport_request_asserted(
    const openref_audio_transport_t *transport);

bool openref_audio_transport_prepare_tx(
    openref_audio_transport_t *transport,
    uint32_t timestamp_us,
    uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES]);

bool openref_audio_transport_accept_rx(
    openref_audio_transport_t *transport,
    const uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES]);

bool openref_audio_transport_pop_audio(
    openref_audio_transport_t *transport,
    openref_audio_link_frame_t *frame);

#ifdef __cplusplus
}
#endif

#endif
