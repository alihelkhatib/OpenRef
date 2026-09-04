#include <stdbool.h>
#include <stdint.h>

#include "board.h"
#include "app.h"
#include "fsl_debug_console.h"
#include "openref_audio_benchmark.h"
#include "openref_rt595_lc3.h"

static openref_rt595_lc3_t codec;
static openref_audio_benchmark_t benchmark;

static uint32_t smoke_clock_us(void *context)
{
    uint32_t *clock = context;
    return (*clock)++;
}

int main(void)
{
    BOARD_InitHardware();
    if (!openref_rt595_lc3_init(&codec)) {
        PRINTF("OPENREF_RT595_SMOKE lc3_init=fail\r\n");
        for (;;) {
        }
    }
    int16_t guard_pcm[OPENREF_AUDIO_FRAME_SAMPLES];
    bool null_plc_rejected = !openref_rt595_lc3_decode(
        &codec, 0u, NULL, true, guard_pcm);
    uint32_t clock_us = 0u;
    /* Four blocks exercise both halves of packet zero and forced PLC in the
     * second half of packet one. Timing remains synthetic in this link smoke. */
    openref_audio_benchmark_config_t config = {0u, 4u, 1u};
    openref_audio_benchmark_hooks_t hooks = {
        openref_rt595_lc3_encode, openref_rt595_lc3_decode, smoke_clock_us,
        &codec, &clock_us,
    };
    bool initialized = openref_audio_benchmark_init(&benchmark, &config, hooks);
    bool processed = initialized;
    for (uint8_t block = 0u; processed && block < config.measured_blocks;
         block++) {
        processed = openref_audio_benchmark_step(&benchmark);
    }
    openref_audio_benchmark_result_t result;
    bool result_available = processed &&
        openref_audio_benchmark_get_result(&benchmark, &result);
    bool passed = null_plc_rejected && result_available &&
        result.complete && result.passed &&
        result.completed_blocks == config.measured_blocks &&
        result.plc_calls != 0u;
    PRINTF("OPENREF_RT595_SMOKE lc3=%s blocks=%u plc=%u encode_fail=%u "
           "decode_fail=%u process_fail=%u benchmark_bytes=%u codec_bytes=%u\r\n",
           passed ? "pass" : "fail",
           result_available ? (unsigned int)result.completed_blocks : 0u,
           result_available ? (unsigned int)result.plc_calls : 0u,
           result_available ? (unsigned int)result.encode_failures : 0u,
           result_available ? (unsigned int)result.decode_failures : 0u,
           result_available ? (unsigned int)result.process_failures : 0u,
           (unsigned int)sizeof(benchmark), (unsigned int)sizeof(codec));
    for (;;) {
    }
}
