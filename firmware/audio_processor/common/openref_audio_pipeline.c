#include "openref_audio_pipeline.h"

#include <stddef.h>
#include <string.h>

bool openref_audio_pipeline_init(
    openref_audio_pipeline_t *pipeline,
    uint8_t local_source_id,
    uint16_t initial_sequence)
{
    if (pipeline == NULL || local_source_id < 1u || local_source_id > 6u) {
        return false;
    }
    memset(pipeline, 0, sizeof(*pipeline));
    pipeline->local_source_id = local_source_id;
    if (!openref_audio_capture_init(&pipeline->capture, local_source_id,
                                    initial_sequence)) {
        return false;
    }
    openref_audio_playout_init(&pipeline->playout);
    openref_audio_mixer_init(&pipeline->mixer);
    return true;
}

bool openref_audio_pipeline_ingest_remote(
    openref_audio_pipeline_t *pipeline,
    const openref_audio_link_frame_t *frame)
{
    if (pipeline == NULL || frame == NULL ||
        frame->source_id == pipeline->local_source_id) {
        return false;
    }
    return openref_audio_playout_push(&pipeline->playout, frame);
}

bool openref_audio_pipeline_render(
    openref_audio_pipeline_t *pipeline,
    openref_audio_decode_fn decode,
    void *decode_context,
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES])
{
    if (pipeline == NULL || decode == NULL || output == NULL) {
        return false;
    }
    int16_t sources[OPENREF_AUDIO_REMOTE_SOURCES][OPENREF_AUDIO_FRAME_SAMPLES];
    uint8_t valid_mask = 0u;
    uint8_t decoder_index = 0u;
    for (uint8_t source_id = 1u; source_id <= 6u; source_id++) {
        if (source_id == pipeline->local_source_id) {
            continue;
        }
        uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES];
        bool use_plc = true;
        bool have_frame = openref_audio_playout_next(
            &pipeline->playout, source_id, codec_frame, &use_plc);
        bool decoded = have_frame && decode(
            decode_context, decoder_index, codec_frame, use_plc,
            sources[decoder_index]);
        if (decoded) {
            valid_mask |= (uint8_t)(1u << decoder_index);
        } else {
            memset(sources[decoder_index], 0,
                   OPENREF_AUDIO_FRAME_SAMPLES * sizeof(int16_t));
            pipeline->decode_failures++;
        }
        decoder_index++;
    }
    openref_audio_mixer_process(&pipeline->mixer, sources, valid_mask, output);
    pipeline->render_blocks++;
    return true;
}
