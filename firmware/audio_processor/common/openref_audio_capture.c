#include "openref_audio_capture.h"

#include <stddef.h>
#include <string.h>

bool openref_audio_capture_init(
    openref_audio_capture_t *capture,
    uint8_t local_source_id,
    uint16_t initial_sequence)
{
    if (capture == NULL || local_source_id < 1u || local_source_id > 6u) {
        return false;
    }
    memset(capture, 0, sizeof(*capture));
    capture->local_source_id = local_source_id;
    capture->next_sequence = initial_sequence;
    openref_audio_link_queue_init(&capture->output_queue);
    return true;
}

bool openref_audio_capture_submit(
    openref_audio_capture_t *capture,
    const uint8_t codec_frame[OPENREF_AUDIO_CAPTURE_CODEC_BYTES],
    bool valid,
    bool discontinuity,
    uint32_t capture_timestamp_us)
{
    if (capture == NULL || (valid && codec_frame == NULL)) {
        return false;
    }
    uint8_t *destination = &capture->pending_payload[
        capture->pending_half * OPENREF_AUDIO_CAPTURE_CODEC_BYTES];
    if (valid) {
        memcpy(destination, codec_frame, OPENREF_AUDIO_CAPTURE_CODEC_BYTES);
        capture->pending_flags |= capture->pending_half == 0u
            ? OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID
            : OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID;
    } else {
        memset(destination, 0, OPENREF_AUDIO_CAPTURE_CODEC_BYTES);
        capture->invalid_codec_frames++;
    }
    if (discontinuity) {
        capture->pending_flags |= OPENREF_AUDIO_LINK_FLAG_DISCONTINUITY;
    }
    if (capture->pending_half == 0u) {
        capture->first_half_timestamp_us = capture_timestamp_us;
        capture->pending_half = 1u;
        capture->codec_frames++;
        return true;
    }

    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_LOCAL_AUDIO,
        .source_id = capture->local_source_id,
        .flags = capture->pending_flags,
        .sequence = capture->next_sequence,
        .timestamp_us = capture->first_half_timestamp_us,
        .producer_queue_depth = capture->output_queue.count,
    };
    memcpy(frame.payload, capture->pending_payload, OPENREF_AUDIO_LINK_PAYLOAD_BYTES);
    bool queued = openref_audio_link_queue_push(&capture->output_queue, &frame);
    capture->next_sequence++;
    capture->pending_half = 0u;
    capture->pending_flags = 0u;
    capture->codec_frames++;
    if (queued) {
        capture->completed_packets++;
    }
    return queued;
}

bool openref_audio_capture_pop(
    openref_audio_capture_t *capture,
    openref_audio_link_frame_t *frame)
{
    if (capture == NULL) {
        return false;
    }
    return openref_audio_link_queue_pop(&capture->output_queue, frame);
}
