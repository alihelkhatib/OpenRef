#ifndef OPENREF_AUDIO_PLAYOUT_H
#define OPENREF_AUDIO_PLAYOUT_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_link.h"

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY 4u
#define OPENREF_AUDIO_CODEC_FRAME_BYTES 40u

typedef struct {
    uint16_t sequence;
    uint8_t flags;
    uint8_t payload[OPENREF_AUDIO_LINK_PAYLOAD_BYTES];
} openref_audio_playout_packet_t;

typedef struct {
    openref_audio_playout_packet_t entries[OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY];
    uint8_t head;
    uint8_t count;
    uint16_t expected_sequence;
    bool expected_valid;
    bool current_loaded;
    uint8_t current_half;
    openref_audio_playout_packet_t current;
    uint32_t accepted;
    uint32_t duplicates;
    uint32_t stale;
    uint32_t overruns;
    uint32_t plc_frames;
    uint32_t delivered_frames;
} openref_audio_playout_source_t;

typedef struct {
    openref_audio_playout_source_t sources[6];
} openref_audio_playout_t;

void openref_audio_playout_init(openref_audio_playout_t *playout);

bool openref_audio_playout_push(
    openref_audio_playout_t *playout,
    const openref_audio_link_frame_t *frame);

bool openref_audio_playout_next(
    openref_audio_playout_t *playout,
    uint8_t source_id,
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool *use_plc);

#ifdef __cplusplus
}
#endif

#endif
