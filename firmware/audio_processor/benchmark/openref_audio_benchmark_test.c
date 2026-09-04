#include <assert.h>
#include <string.h>

#include "openref_audio_benchmark.h"

typedef struct {
    uint32_t now_us;
    uint32_t encode_us;
    uint32_t decode_us;
    uint32_t encode_calls;
    uint32_t decode_calls;
    uint32_t decoder_calls[OPENREF_AUDIO_REMOTE_SOURCES];
    uint32_t plc_calls;
    uint32_t fail_encode_call;
    uint32_t fail_decode_call;
    bool fast_codec;
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
    if (target->encode_calls == target->fail_encode_call) {
        return false;
    }
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
    assert(decoder_index < OPENREF_AUDIO_REMOTE_SOURCES);
    target->decoder_calls[decoder_index]++;
    if (target->decode_calls == target->fail_decode_call) {
        return false;
    }
    target->plc_calls += use_plc ? 1u : 0u;
    if (target->fast_codec) {
        pcm[0] = use_plc ? 0 : (int16_t)(frame[0] + decoder_index);
        return true;
    }
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
    assert(result.plc_calls == 2u);
    assert(target.encode_calls == 11u);
    assert(target.decode_calls == 50u);
    for (uint8_t decoder = 0u; decoder < OPENREF_AUDIO_REMOTE_SOURCES;
         decoder++) {
        assert(target.decoder_calls[decoder] == 10u);
    }
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

static void test_timer_wraparound(void)
{
    fake_target_t target = {
        .now_us = UINT32_MAX - 500u,
        .encode_us = 100u,
        .decode_us = 200u,
    };
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_config_t config = {0u, 1u, 1u};
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, &config, hooks));
    assert(openref_audio_benchmark_step(&benchmark));
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(result.maximum_total_us == 1100u);
    assert(result.complete && !result.passed);
    assert(result.plc_calls == 0u);
}

static void test_warmup_plc_does_not_satisfy_measured_workload(void)
{
    fake_target_t target = {.encode_us = 100u, .decode_us = 200u};
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_config_t config = {
        .warmup_blocks = 4u,
        .measured_blocks = 1u,
        .plc_period_packets = 1u,
    };
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, &config, hooks));
    for (uint8_t index = 0u; index < 5u; index++) {
        assert(openref_audio_benchmark_step(&benchmark));
    }
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(target.plc_calls == 1u);
    assert(result.plc_calls == 0u);
    assert(result.complete && !result.passed);
}

static void test_codec_failure_fails_result(void)
{
    fake_target_t target = {
        .encode_us = 100u,
        .decode_us = 200u,
        .fail_decode_call = 3u,
    };
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_config_t config = {0u, 1u, 1u};
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, &config, hooks));
    assert(openref_audio_benchmark_step(&benchmark));
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(result.complete && !result.passed);
    assert(result.decode_failures == 1u);
}

static void test_diagnostic_counters_saturate(void)
{
    fake_target_t target = {
        .encode_us = 100u,
        .decode_us = 200u,
        .fail_decode_call = 1u,
    };
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_config_t config = {0u, 1u, 1u};
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, &config, hooks));
    benchmark.result.decode_failures = UINT32_MAX;
    assert(openref_audio_benchmark_step(&benchmark));
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(result.decode_failures == UINT32_MAX);
    assert(result.complete && !result.passed);
}

static void test_invalid_configuration(void)
{
    fake_target_t target = {0};
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_t benchmark;
    openref_audio_benchmark_config_t no_measurement = {0u, 0u, 1u};
    openref_audio_benchmark_config_t no_plc = {0u, 1u, 0u};
    assert(!openref_audio_benchmark_init(&benchmark, &no_measurement, hooks));
    assert(!openref_audio_benchmark_init(&benchmark, &no_plc, hooks));
    hooks.clock_us = NULL;
    assert(!openref_audio_benchmark_init(&benchmark, NULL, hooks));
}

static void test_canonical_workload_schedule(void)
{
    fake_target_t target = {
        .encode_us = 100u,
        .decode_us = 200u,
        .fast_codec = true,
    };
    openref_audio_benchmark_hooks_t hooks = {
        encode, decode, clock_us, &target, &target,
    };
    openref_audio_benchmark_t benchmark;
    assert(openref_audio_benchmark_init(&benchmark, NULL, hooks));
    const uint32_t total = OPENREF_AUDIO_BENCHMARK_DEFAULT_WARMUP_BLOCKS +
        OPENREF_AUDIO_BENCHMARK_DEFAULT_MEASURED_BLOCKS;
    for (uint32_t block = 0u; block < total; block++) {
        assert(openref_audio_benchmark_step(&benchmark));
    }
    openref_audio_benchmark_result_t result;
    assert(openref_audio_benchmark_get_result(&benchmark, &result));
    assert(result.complete && result.passed);
    assert(result.completed_blocks == 180000u);
    assert(result.plc_calls == 927u);
    assert(target.encode_calls == total + 1u);
    assert(target.decode_calls == total * OPENREF_AUDIO_REMOTE_SOURCES);
}

int main(void)
{
    test_complete_passing_run();
    test_deadline_failure();
    test_timer_wraparound();
    test_warmup_plc_does_not_satisfy_measured_workload();
    test_codec_failure_fails_result();
    test_diagnostic_counters_saturate();
    test_invalid_configuration();
    test_canonical_workload_schedule();
    return 0;
}
