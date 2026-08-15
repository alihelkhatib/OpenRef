#ifndef OPENREF_AUDIO_BENCHMARK_H
#define OPENREF_AUDIO_BENCHMARK_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_runtime.h"

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_AUDIO_BENCHMARK_VERSION 1u
#define OPENREF_AUDIO_BENCHMARK_DEFAULT_WARMUP_BLOCKS 1000u
#define OPENREF_AUDIO_BENCHMARK_DEFAULT_MEASURED_BLOCKS 180000u
#define OPENREF_AUDIO_BENCHMARK_DEFAULT_PLC_PERIOD_PACKETS 97u

typedef bool (*openref_benchmark_encode_fn)(
    void *context,
    const int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES]);

typedef bool (*openref_benchmark_decode_fn)(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES]);

typedef struct {
    openref_benchmark_encode_fn encode;
    openref_benchmark_decode_fn decode;
    openref_audio_clock_us_fn clock_us;
    void *codec_context;
    void *clock_context;
} openref_audio_benchmark_hooks_t;

typedef struct {
    uint32_t warmup_blocks;
    uint32_t measured_blocks;
    uint16_t plc_period_packets;
} openref_audio_benchmark_config_t;

typedef struct {
    uint32_t version;
    uint32_t requested_blocks;
    uint32_t completed_blocks;
    uint32_t plc_calls;
    uint32_t encode_failures;
    uint32_t decode_failures;
    uint32_t process_failures;
    uint32_t deadline_misses;
    uint32_t maximum_encode_us;
    uint32_t maximum_render_us;
    uint32_t maximum_total_us;
    uint32_t average_encode_us;
    uint32_t average_render_us;
    uint32_t average_total_us;
    bool complete;
    bool passed;
} openref_audio_benchmark_result_t;

typedef struct {
    openref_audio_runtime_t runtime;
    openref_audio_benchmark_hooks_t hooks;
    openref_audio_benchmark_config_t config;
    openref_audio_benchmark_result_t result;
    uint8_t latest_codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES];
    uint32_t total_blocks;
    uint32_t prng_state;
    uint64_t encode_sum_us;
    uint64_t render_sum_us;
    uint64_t total_sum_us;
    bool initialized;
} openref_audio_benchmark_t;

bool openref_audio_benchmark_init(
    openref_audio_benchmark_t *benchmark,
    const openref_audio_benchmark_config_t *config,
    openref_audio_benchmark_hooks_t hooks);

bool openref_audio_benchmark_step(openref_audio_benchmark_t *benchmark);

bool openref_audio_benchmark_get_result(
    openref_audio_benchmark_t *benchmark,
    openref_audio_benchmark_result_t *result);

#ifdef __cplusplus
}
#endif

#endif
