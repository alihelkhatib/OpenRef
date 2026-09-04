#include "openref_audio_benchmark.h"

#include <stddef.h>
#include <string.h>

static void update_maximum(uint32_t value, uint32_t *maximum)
{
    if (value > *maximum) {
        *maximum = value;
    }
}

static void increment_saturating(uint32_t *value)
{
    if (*value != UINT32_MAX) {
        (*value)++;
    }
}

static uint32_t next_random(openref_audio_benchmark_t *benchmark)
{
    uint32_t value = benchmark->prng_state;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    benchmark->prng_state = value;
    return value;
}

static void fill_microphone(
    openref_audio_benchmark_t *benchmark,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES])
{
    for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
        uint32_t random = next_random(benchmark);
        int32_t noise = (int32_t)(random & 0x0fffu) - 2048;
        int32_t triangle = (int32_t)((benchmark->total_blocks * 17u + index * 97u) &
                                     0x3fffu);
        if (triangle >= 8192) {
            triangle = 16383 - triangle;
        }
        triangle = (triangle - 4096) * 3;
        pcm[index] = (int16_t)(triangle + noise);
    }
}

static bool benchmark_encode(
    void *context,
    const int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES])
{
    openref_audio_benchmark_t *benchmark = context;
    bool encoded = benchmark->hooks.encode(
        benchmark->hooks.codec_context, pcm, codec_frame);
    if (encoded) {
        memcpy(benchmark->latest_codec_frame, codec_frame,
               OPENREF_AUDIO_CODEC_FRAME_BYTES);
    } else {
        increment_saturating(&benchmark->result.encode_failures);
    }
    return encoded;
}

static bool benchmark_decode(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES])
{
    openref_audio_benchmark_t *benchmark = context;
    /* Promotion evidence must reflect the measured interval, not warmup. */
    if (use_plc &&
        benchmark->total_blocks >= benchmark->config.warmup_blocks) {
        increment_saturating(&benchmark->result.plc_calls);
    }
    bool decoded = benchmark->hooks.decode(
        benchmark->hooks.codec_context, decoder_index, codec_frame, use_plc, pcm);
    if (!decoded) {
        increment_saturating(&benchmark->result.decode_failures);
    }
    return decoded;
}

static bool queue_remote_packets(openref_audio_benchmark_t *benchmark)
{
    if ((benchmark->total_blocks & 1u) != 0u) {
        return true;
    }
    uint16_t packet_sequence = (uint16_t)(benchmark->total_blocks / 2u);
    for (uint8_t source_id = 2u; source_id <= 6u; source_id++) {
        openref_audio_link_frame_t frame = {
            .kind = OPENREF_AUDIO_LINK_REMOTE_AUDIO,
            .source_id = source_id,
            .flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                     OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID,
            .sequence = packet_sequence,
            .timestamp_us = benchmark->total_blocks * OPENREF_AUDIO_BLOCK_INTERVAL_US,
        };
        if (source_id == 6u && benchmark->config.plc_period_packets != 0u &&
            packet_sequence != 0u &&
            packet_sequence % benchmark->config.plc_period_packets == 0u) {
            frame.flags &= (uint8_t)~OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID;
        }
        memcpy(&frame.payload[0], benchmark->latest_codec_frame,
               OPENREF_AUDIO_CODEC_FRAME_BYTES);
        memcpy(&frame.payload[OPENREF_AUDIO_CODEC_FRAME_BYTES],
               benchmark->latest_codec_frame, OPENREF_AUDIO_CODEC_FRAME_BYTES);
        if (!openref_audio_runtime_ingest_remote(&benchmark->runtime, &frame)) {
            return false;
        }
    }
    return true;
}

static void finalize(openref_audio_benchmark_t *benchmark)
{
    uint32_t blocks = benchmark->result.completed_blocks;
    if (blocks != 0u) {
        benchmark->result.average_encode_us =
            (uint32_t)(benchmark->encode_sum_us / blocks);
        benchmark->result.average_render_us =
            (uint32_t)(benchmark->render_sum_us / blocks);
        benchmark->result.average_total_us =
            (uint32_t)(benchmark->total_sum_us / blocks);
    }
    benchmark->result.complete = blocks == benchmark->result.requested_blocks;
    benchmark->result.passed = benchmark->result.complete &&
        benchmark->result.plc_calls != 0u &&
        benchmark->result.encode_failures == 0u &&
        benchmark->result.decode_failures == 0u &&
        benchmark->result.process_failures == 0u &&
        benchmark->result.deadline_misses == 0u &&
        benchmark->result.maximum_total_us <= OPENREF_AUDIO_PROCESSING_BUDGET_US;
    benchmark->finished = true;
}

bool openref_audio_benchmark_init(
    openref_audio_benchmark_t *benchmark,
    const openref_audio_benchmark_config_t *config,
    openref_audio_benchmark_hooks_t hooks)
{
    if (benchmark == NULL || hooks.encode == NULL || hooks.decode == NULL ||
        hooks.clock_us == NULL) {
        return false;
    }
    openref_audio_benchmark_config_t selected = {
        .warmup_blocks = OPENREF_AUDIO_BENCHMARK_DEFAULT_WARMUP_BLOCKS,
        .measured_blocks = OPENREF_AUDIO_BENCHMARK_DEFAULT_MEASURED_BLOCKS,
        .plc_period_packets = OPENREF_AUDIO_BENCHMARK_DEFAULT_PLC_PERIOD_PACKETS,
    };
    if (config != NULL) {
        selected = *config;
    }
    if (selected.measured_blocks == 0u || selected.plc_period_packets == 0u ||
        selected.warmup_blocks > UINT32_MAX - selected.measured_blocks) {
        return false;
    }
    memset(benchmark, 0, sizeof(*benchmark));
    benchmark->hooks = hooks;
    benchmark->config = selected;
    benchmark->prng_state = 0x4f524246u;
    benchmark->result.version = OPENREF_AUDIO_BENCHMARK_VERSION;
    benchmark->result.requested_blocks = selected.measured_blocks;
    if (!openref_audio_runtime_init(&benchmark->runtime, 1u, 0u)) {
        return false;
    }
    int16_t seed_pcm[OPENREF_AUDIO_FRAME_SAMPLES];
    fill_microphone(benchmark, seed_pcm);
    if (!hooks.encode(hooks.codec_context, seed_pcm,
                      benchmark->latest_codec_frame)) {
        return false;
    }
    benchmark->initialized = true;
    return true;
}

bool openref_audio_benchmark_step(openref_audio_benchmark_t *benchmark)
{
    if (benchmark == NULL || !benchmark->initialized || benchmark->finished) {
        return false;
    }
    if (!queue_remote_packets(benchmark)) {
        increment_saturating(&benchmark->result.process_failures);
        finalize(benchmark);
        return false;
    }
    int16_t microphone[OPENREF_AUDIO_FRAME_SAMPLES];
    int16_t headphone[OPENREF_AUDIO_FRAME_SAMPLES];
    fill_microphone(benchmark, microphone);
    bool processed = openref_audio_runtime_process(
        &benchmark->runtime, microphone,
        benchmark->total_blocks * OPENREF_AUDIO_BLOCK_INTERVAL_US,
        benchmark_encode, benchmark_decode, benchmark->hooks.clock_us,
        benchmark, benchmark->hooks.clock_context, headphone);
    if (!processed) {
        increment_saturating(&benchmark->result.process_failures);
        finalize(benchmark);
        return false;
    }

    if (benchmark->total_blocks >= benchmark->config.warmup_blocks) {
        benchmark->result.completed_blocks++;
        benchmark->encode_sum_us += benchmark->runtime.last_encode_us;
        benchmark->render_sum_us += benchmark->runtime.last_render_us;
        benchmark->total_sum_us += benchmark->runtime.last_total_us;
        update_maximum(benchmark->runtime.last_encode_us,
                       &benchmark->result.maximum_encode_us);
        update_maximum(benchmark->runtime.last_render_us,
                       &benchmark->result.maximum_render_us);
        update_maximum(benchmark->runtime.last_total_us,
                       &benchmark->result.maximum_total_us);
        if (benchmark->runtime.last_total_us > OPENREF_AUDIO_PROCESSING_BUDGET_US) {
            increment_saturating(&benchmark->result.deadline_misses);
        }
    }
    benchmark->total_blocks++;
    if (benchmark->result.completed_blocks == benchmark->config.measured_blocks) {
        finalize(benchmark);
    }
    return true;
}

bool openref_audio_benchmark_get_result(
    openref_audio_benchmark_t *benchmark,
    openref_audio_benchmark_result_t *result)
{
    if (benchmark == NULL || result == NULL || !benchmark->initialized) {
        return false;
    }
    if (benchmark->result.completed_blocks != 0u && !benchmark->result.complete) {
        uint32_t blocks = benchmark->result.completed_blocks;
        benchmark->result.average_encode_us =
            (uint32_t)(benchmark->encode_sum_us / blocks);
        benchmark->result.average_render_us =
            (uint32_t)(benchmark->render_sum_us / blocks);
        benchmark->result.average_total_us =
            (uint32_t)(benchmark->total_sum_us / blocks);
    }
    *result = benchmark->result;
    return true;
}
