#ifndef OPENREF_AUDIO_CAPTURE_H
#define OPENREF_AUDIO_CAPTURE_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_link.h"

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_AUDIO_CAPTURE_CODEC_BYTES 40u

typedef struct {
    uint8_t local_source_id;
    uint8_t pending_half;
    uint8_t pending_flags;
    uint16_t next_sequence;
    uint32_t first_half_timestamp_us;
    uint8_t pending_payload[OPENREF_AUDIO_LINK_PAYLOAD_BYTES];
    openref_audio_link_queue_t output_queue;
    uint32_t codec_frames;
    uint32_t invalid_codec_frames;
    uint32_t completed_packets;
} openref_audio_capture_t;

bool openref_audio_capture_init(
    openref_audio_capture_t *capture,
    uint8_t local_source_id,
    uint16_t initial_sequence);

bool openref_audio_capture_submit(
    openref_audio_capture_t *capture,
    const uint8_t codec_frame[OPENREF_AUDIO_CAPTURE_CODEC_BYTES],
    bool valid,
    bool discontinuity,
    uint32_t capture_timestamp_us);

bool openref_audio_capture_pop(
    openref_audio_capture_t *capture,
    openref_audio_link_frame_t *frame);

#ifdef __cplusplus
}
#endif

#endif
