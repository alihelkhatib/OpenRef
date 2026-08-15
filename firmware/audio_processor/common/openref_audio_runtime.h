#ifndef OPENREF_AUDIO_RUNTIME_H
#define OPENREF_AUDIO_RUNTIME_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_pipeline.h"

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_AUDIO_BLOCK_INTERVAL_US 10000u
#define OPENREF_AUDIO_PROCESSING_BUDGET_US 8000u

typedef bool (*openref_audio_encode_fn)(
    void *context,
    const int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES]);

typedef uint32_t (*openref_audio_clock_us_fn)(void *context);

typedef struct {
    openref_audio_pipeline_t pipeline;
    uint32_t previous_capture_timestamp_us;
    bool have_previous_capture;
    uint32_t processed_blocks;
    uint32_t capture_discontinuities;
    uint32_t encode_failures;
    uint32_t deadline_misses;
    uint32_t last_encode_us;
    uint32_t maximum_encode_us;
    uint32_t last_render_us;
    uint32_t maximum_render_us;
    uint32_t last_total_us;
    uint32_t maximum_total_us;
} openref_audio_runtime_t;

bool openref_audio_runtime_init(
    openref_audio_runtime_t *runtime,
    uint8_t local_source_id,
    uint16_t initial_sequence);

bool openref_audio_runtime_process(
    openref_audio_runtime_t *runtime,
    const int16_t microphone_pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint32_t capture_timestamp_us,
    openref_audio_encode_fn encode,
    openref_audio_decode_fn decode,
    openref_audio_clock_us_fn clock_us,
    void *codec_context,
    void *clock_context,
    int16_t headphone_pcm[OPENREF_AUDIO_FRAME_SAMPLES]);

bool openref_audio_runtime_ingest_remote(
    openref_audio_runtime_t *runtime,
    const openref_audio_link_frame_t *frame);

bool openref_audio_runtime_take_local(
    openref_audio_runtime_t *runtime,
    openref_audio_link_frame_t *frame);

#ifdef __cplusplus
}
#endif

#endif
