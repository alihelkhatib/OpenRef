#include "openref_audio_runtime.h"

#include <stddef.h>

static void update_maximum(uint32_t value, uint32_t *maximum)
{
    if (value > *maximum) {
        *maximum = value;
    }
}

bool openref_audio_runtime_init(
    openref_audio_runtime_t *runtime,
    uint8_t local_source_id,
    uint16_t initial_sequence)
{
    if (runtime == NULL) {
        return false;
    }
    *runtime = (openref_audio_runtime_t){0};
    return openref_audio_pipeline_init(
        &runtime->pipeline, local_source_id, initial_sequence);
}

bool openref_audio_runtime_process(
    openref_audio_runtime_t *runtime,
    const int16_t microphone_pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint32_t capture_timestamp_us,
    openref_audio_encode_fn encode,
    openref_audio_decode_fn decode,
    openref_audio_clock_us_fn clock_us,
    void *codec_context,
    void *clock_context,
    int16_t headphone_pcm[OPENREF_AUDIO_FRAME_SAMPLES])
{
    if (runtime == NULL || microphone_pcm == NULL || encode == NULL ||
        decode == NULL || clock_us == NULL || headphone_pcm == NULL) {
        return false;
    }

    bool discontinuity = runtime->have_previous_capture &&
        (capture_timestamp_us - runtime->previous_capture_timestamp_us !=
         OPENREF_AUDIO_BLOCK_INTERVAL_US);
    if (discontinuity) {
        runtime->capture_discontinuities++;
    }
    runtime->previous_capture_timestamp_us = capture_timestamp_us;
    runtime->have_previous_capture = true;

    uint32_t start_us = clock_us(clock_context);
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES];
    bool encoded = encode(codec_context, microphone_pcm, codec_frame);
    uint32_t after_encode_us = clock_us(clock_context);
    runtime->last_encode_us = after_encode_us - start_us;
    update_maximum(runtime->last_encode_us, &runtime->maximum_encode_us);
    if (!encoded) {
        runtime->encode_failures++;
    }
    if (!openref_audio_capture_submit(
            &runtime->pipeline.capture, codec_frame, encoded, discontinuity,
            capture_timestamp_us)) {
        return false;
    }

    if (!openref_audio_pipeline_render(
            &runtime->pipeline, decode, codec_context, headphone_pcm)) {
        return false;
    }
    uint32_t finish_us = clock_us(clock_context);
    runtime->last_render_us = finish_us - after_encode_us;
    runtime->last_total_us = finish_us - start_us;
    update_maximum(runtime->last_render_us, &runtime->maximum_render_us);
    update_maximum(runtime->last_total_us, &runtime->maximum_total_us);
    if (runtime->last_total_us > OPENREF_AUDIO_PROCESSING_BUDGET_US) {
        runtime->deadline_misses++;
    }
    runtime->processed_blocks++;
    return true;
}

bool openref_audio_runtime_ingest_remote(
    openref_audio_runtime_t *runtime,
    const openref_audio_link_frame_t *frame)
{
    return runtime != NULL &&
        openref_audio_pipeline_ingest_remote(&runtime->pipeline, frame);
}

bool openref_audio_runtime_take_local(
    openref_audio_runtime_t *runtime,
    openref_audio_link_frame_t *frame)
{
    return runtime != NULL && frame != NULL &&
        openref_audio_capture_pop(&runtime->pipeline.capture, frame);
}
