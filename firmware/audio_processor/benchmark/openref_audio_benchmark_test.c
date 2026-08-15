#include <assert.h>
#include <string.h>

#include "openref_audio_benchmark.h"

typedef struct {
    uint32_t now_us;
    uint32_t encode_us;
    uint32_t decode_us;
    uint32_t encode_calls;
    uint32_t decode_calls;
    uint32_t plc_calls;
} fake_target_t;

static uint32_t clock_us(void *context)
{
    return ((fake_target_t *)context)->now_us;
}

static bool encode(void *context, const int16_t *pcm, uint8_t *frame)
{
    fake_target_t *target = context;
    target->now_us += target->encode_us;
    target->encode_calls++;
    for (uint8_t index = 0u; index < OPENREF_AUDIO_CODEC_FRAME_BYTES; index++) {
        frame[index] = (uint8_t)(pcm[index] ^ index);
    }
    return true;
}

static bool decode(
    void *context,
    uint8_t decoder_index,
    const uint8_t *frame,
    bool use_plc,
    int16_t *pcm)
{
    fake_target_t *target = context;
    target->now_us += target->decode_us;
    target->decode_calls++;
    target->plc_calls += use_plc ? 1u : 0u;
    for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
        pcm[index] = use_plc ? 0 : (int16_t)(frame[index % 40u] + decoder_index);
    }
    return true;
}

static void test_complete_passing_run(void)
{
    fake_target_t target = {.encode_us = 100u, .decode_us = 200u};
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_config_t config = {
        .warmup_blocks = 2u,
        .measured_blocks = 8u,
        .plc_period_packets = 2u,
    };
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, &config, hooks));
    for (uint8_t index = 0u; index < 10u; index++) {
        assert(openref_audio_benchmark_step(&benchmark));
    }
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(result.complete && result.passed);
    assert(result.completed_blocks == 8u);
    assert(result.maximum_encode_us == 100u);
    assert(result.maximum_render_us == 1000u);
    assert(result.maximum_total_us == 1100u);
    assert(result.average_total_us == 1100u);
    assert(result.plc_calls != 0u);
    assert(target.encode_calls == 11u);
    assert(target.decode_calls == 50u);
    assert(!openref_audio_benchmark_step(&benchmark));
}

static void test_deadline_failure(void)
{
    fake_target_t target = {.encode_us = 4000u, .decode_us = 1000u};
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_config_t config = {
        .warmup_blocks = 0u,
        .measured_blocks = 4u,
        .plc_period_packets = 1u,
    };
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, &config, hooks));
    for (uint8_t index = 0u; index < 4u; index++) {
        assert(openref_audio_benchmark_step(&benchmark));
    }
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(result.complete && !result.passed);
    assert(result.deadline_misses == 4u);
    assert(result.maximum_total_us == 9000u);
}

int main(void)
{
    test_complete_passing_run();
    test_deadline_failure();
    return 0;
}
