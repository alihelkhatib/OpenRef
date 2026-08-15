#ifndef OPENREF_AUDIO_PIPELINE_H
#define OPENREF_AUDIO_PIPELINE_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_capture.h"
#include "openref_audio_mixer.h"
#include "openref_audio_playout.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef bool (*openref_audio_decode_fn)(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES]);

typedef struct {
    uint8_t local_source_id;
    openref_audio_capture_t capture;
    openref_audio_playout_t playout;
    openref_audio_mixer_t mixer;
    uint32_t render_blocks;
    uint32_t decode_failures;
} openref_audio_pipeline_t;

bool openref_audio_pipeline_init(
    openref_audio_pipeline_t *pipeline,
    uint8_t local_source_id,
    uint16_t initial_sequence);

bool openref_audio_pipeline_ingest_remote(
    openref_audio_pipeline_t *pipeline,
    const openref_audio_link_frame_t *frame);

bool openref_audio_pipeline_render(
    openref_audio_pipeline_t *pipeline,
    openref_audio_decode_fn decode,
    void *decode_context,
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES]);

#ifdef __cplusplus
}
#endif

#endif
