#include "openref_audio_playout.h"

#include <stddef.h>
#include <string.h>

static bool sequence_after(uint16_t candidate, uint16_t reference)
{
    return (int16_t)(candidate - reference) > 0;
}

static void discard_stale_front(openref_audio_playout_source_t *source)
{
    while (source->count > 0u && source->expected_valid) {
        uint16_t sequence = source->entries[source->head].sequence;
        if (sequence == source->expected_sequence ||
            sequence_after(sequence, source->expected_sequence)) {
            return;
        }
        source->head = (uint8_t)((source->head + 1u) %
                                 OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY);
        source->count--;
        source->stale++;
    }
}

void openref_audio_playout_init(openref_audio_playout_t *playout)
{
    if (playout != NULL) {
        memset(playout, 0, sizeof(*playout));
    }
}

bool openref_audio_playout_push(
    openref_audio_playout_t *playout,
    const openref_audio_link_frame_t *frame)
{
    if (playout == NULL || frame == NULL ||
        frame->kind != OPENREF_AUDIO_LINK_REMOTE_AUDIO ||
        frame->source_id < 1u || frame->source_id > 6u) {
        return false;
    }
    openref_audio_playout_source_t *source = &playout->sources[frame->source_id - 1u];
    if (source->expected_valid && frame->sequence != source->expected_sequence &&
        !sequence_after(frame->sequence, source->expected_sequence)) {
        source->stale++;
        return false;
    }
    for (uint8_t offset = 0u; offset < source->count; offset++) {
        uint8_t index = (uint8_t)((source->head + offset) %
                                  OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY);
        if (source->entries[index].sequence == frame->sequence) {
            source->duplicates++;
            return false;
        }
    }
    if (source->count > 0u) {
        uint8_t tail_index = (uint8_t)((source->head + source->count - 1u) %
                                       OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY);
        if (!sequence_after(frame->sequence, source->entries[tail_index].sequence)) {
            source->stale++;
            return false;
        }
    }
    if (source->count == OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY) {
        source->head = (uint8_t)((source->head + 1u) %
                                 OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY);
        source->count--;
        source->overruns++;
    }
    uint8_t tail = (uint8_t)((source->head + source->count) %
                             OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY);
    source->entries[tail].sequence = frame->sequence;
    source->entries[tail].flags = frame->flags;
    memcpy(source->entries[tail].payload, frame->payload,
           OPENREF_AUDIO_LINK_PAYLOAD_BYTES);
    source->count++;
    source->accepted++;
    return true;
}

bool openref_audio_playout_next(
    openref_audio_playout_t *playout,
    uint8_t source_id,
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool *use_plc)
{
    if (playout == NULL || codec_frame == NULL || use_plc == NULL ||
        source_id < 1u || source_id > 6u) {
        return false;
    }
    openref_audio_playout_source_t *source = &playout->sources[source_id - 1u];
    if (!source->expected_valid) {
        if (source->count == 0u) {
            memset(codec_frame, 0, OPENREF_AUDIO_CODEC_FRAME_BYTES);
            *use_plc = true;
            source->plc_frames++;
            return true;
        }
        source->expected_sequence = source->entries[source->head].sequence;
        source->expected_valid = true;
    }

    if (source->current_half == 0u) {
        discard_stale_front(source);
        source->current_loaded = false;
        if (source->count > 0u &&
            source->entries[source->head].sequence == source->expected_sequence) {
            source->current = source->entries[source->head];
            source->head = (uint8_t)((source->head + 1u) %
                                     OPENREF_AUDIO_PLAYOUT_QUEUE_CAPACITY);
            source->count--;
            source->current_loaded = true;
        }
    }

    uint8_t validity_flag = source->current_half == 0u
        ? OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID
        : OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID;
    bool valid = source->current_loaded &&
        (source->current.flags & validity_flag) != 0u;
    if (valid) {
        memcpy(codec_frame,
               &source->current.payload[source->current_half * OPENREF_AUDIO_CODEC_FRAME_BYTES],
               OPENREF_AUDIO_CODEC_FRAME_BYTES);
        *use_plc = false;
        source->delivered_frames++;
    } else {
        memset(codec_frame, 0, OPENREF_AUDIO_CODEC_FRAME_BYTES);
        *use_plc = true;
        source->plc_frames++;
    }

    source->current_half++;
    if (source->current_half == 2u) {
        source->current_half = 0u;
        source->current_loaded = false;
        source->expected_sequence++;
    }
    return true;
}
