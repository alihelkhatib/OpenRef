#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_pipeline.h"

typedef struct {
    uint8_t calls;
    uint8_t plc_calls;
} decoder_probe_t;

static bool decode_probe(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES])
{
    decoder_probe_t *probe = context;
    probe->calls++;
    if (use_plc) {
        probe->plc_calls++;
    }
    for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
        pcm[index] = use_plc ? 0 : (int16_t)(codec_frame[0] + decoder_index);
    }
    return true;
}

int main(void)
{
    openref_audio_pipeline_t pipeline;
    assert(openref_audio_pipeline_init(&pipeline, 1u, 0u));
    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_REMOTE_AUDIO,
        .source_id = 2u,
        .flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                 OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID,
        .sequence = 1u,
    };
    frame.payload[0] = 20u;
    frame.payload[40] = 40u;
    assert(openref_audio_pipeline_ingest_remote(&pipeline, &frame));
    assert(!openref_audio_pipeline_ingest_remote(&pipeline, &frame));
    frame.source_id = 1u;
    assert(!openref_audio_pipeline_ingest_remote(&pipeline, &frame));

    decoder_probe_t probe = {0};
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES];
    assert(openref_audio_pipeline_render(&pipeline, decode_probe, &probe, output));
    assert(probe.calls == 5u);
    assert(probe.plc_calls == 4u);
    assert(output[0] == 10);
    assert(pipeline.render_blocks == 1u);
    return 0;
}
