#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_runtime.h"

typedef struct {
    uint32_t now_us;
    uint32_t encode_duration_us;
    uint32_t decode_duration_us;
    bool encode_ok;
} runtime_probe_t;

static uint32_t probe_clock(void *context)
{
    return ((runtime_probe_t *)context)->now_us;
}

static bool probe_encode(
    void *context,
    const int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES])
{
    runtime_probe_t *probe = context;
    probe->now_us += probe->encode_duration_us;
    for (uint8_t index = 0u; index < OPENREF_AUDIO_CODEC_FRAME_BYTES; index++) {
        codec_frame[index] = (uint8_t)(pcm[0] + index);
    }
    return probe->encode_ok;
}

static bool probe_decode(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES])
{
    runtime_probe_t *probe = context;
    probe->now_us += probe->decode_duration_us;
    for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
        pcm[index] = use_plc ? 0 : (int16_t)(codec_frame[0] + decoder_index);
    }
    return true;
}

int main(void)
{
    openref_audio_runtime_t runtime;
    runtime_probe_t probe = {
        .encode_duration_us = 1000u,
        .decode_duration_us = 500u,
        .encode_ok = true,
    };
    int16_t microphone[OPENREF_AUDIO_FRAME_SAMPLES] = {7};
    int16_t headphone[OPENREF_AUDIO_FRAME_SAMPLES];
    assert(openref_audio_runtime_init(&runtime, 1u, 10u));
    assert(openref_audio_runtime_process(
        &runtime, microphone, 10000u, probe_encode, probe_decode,
        probe_clock, &probe, &probe, headphone));
    assert(runtime.processed_blocks == 1u);
    assert(runtime.last_encode_us == 1000u);
    assert(runtime.last_render_us == 2500u);
    assert(runtime.last_total_us == 3500u);
    assert(runtime.deadline_misses == 0u);

    probe.encode_ok = false;
    assert(openref_audio_runtime_process(
        &runtime, microphone, 21000u, probe_encode, probe_decode,
        probe_clock, &probe, &probe, headphone));
    assert(runtime.capture_discontinuities == 1u);
    assert(runtime.encode_failures == 1u);
    openref_audio_link_frame_t local;
    assert(openref_audio_runtime_take_local(&runtime, &local));
    assert(local.sequence == 10u);
    assert(local.flags == (OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                           OPENREF_AUDIO_LINK_FLAG_DISCONTINUITY));

    probe.encode_duration_us = 9000u;
    probe.encode_ok = true;
    assert(openref_audio_runtime_process(
        &runtime, microphone, 31000u, probe_encode, probe_decode,
        probe_clock, &probe, &probe, headphone));
    assert(runtime.deadline_misses == 1u);
    assert(runtime.maximum_total_us == 11500u);
    return 0;
}
