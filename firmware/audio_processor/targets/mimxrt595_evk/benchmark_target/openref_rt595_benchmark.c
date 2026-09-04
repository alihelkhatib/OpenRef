#include <stdbool.h>
#include <stdint.h>

#include "app.h"
#include "board.h"
#include "fsl_clock.h"
#include "fsl_common.h"
#include "fsl_ctimer.h"
#include "fsl_debug_console.h"
#include "openref_audio_benchmark.h"
#include "openref_rt595_lc3.h"
#include "openref_rt595_watchdog.h"
#include "openref_watchdog_gate.h"

#ifndef OPENREF_FIRMWARE_COMMIT
#define OPENREF_FIRMWARE_COMMIT unknown
#endif
#ifndef OPENREF_BOARD_REVISION
#define OPENREF_BOARD_REVISION unknown
#endif
#ifndef OPENREF_IDLE_CURRENT_MA
#define OPENREF_IDLE_CURRENT_MA null
#endif
#ifndef OPENREF_ONE_TALKER_CURRENT_MA
#define OPENREF_ONE_TALKER_CURRENT_MA null
#endif
#ifndef OPENREF_SIX_TALKER_CURRENT_MA
#define OPENREF_SIX_TALKER_CURRENT_MA null
#endif
#ifndef OPENREF_CURRENT_MEASUREMENT
#define OPENREF_CURRENT_MEASUREMENT not_measured
#endif

#define STRINGIFY_INNER(value) #value
#define STRINGIFY(value) STRINGIFY_INNER(value)
#define OPENREF_TIMER_HZ 1000000u
#define OPENREF_PACING_TICKS 10000u
#define OPENREF_STACK_PATTERN 0xa5a5a5a5u
#define OPENREF_WATCHDOG_TIMEOUT_MS 250u
#define OPENREF_WATCHDOG_TASK_TIMEOUT_MS 50u

extern uint32_t __StackTop;
extern uint32_t __StackLimit;

static openref_rt595_lc3_t codec;
static openref_audio_benchmark_t benchmark;
static volatile uint32_t pacing_ticks;
static uint32_t timing_clock_hz;
static openref_watchdog_gate_t watchdog_gate;

static void pacing_callback(uint32_t flags)
{
    (void)flags;
    pacing_ticks++;
}

static ctimer_callback_t pacing_callbacks[] = {
    pacing_callback, NULL, NULL, NULL, NULL, NULL, NULL, NULL};

static uint32_t benchmark_clock_us(void *context)
{
    (void)context;
    return CTIMER_GetTimerCountValue(CTIMER0);
}

static uint64_t benchmark_clock_ms(void)
{
    return (uint64_t)benchmark_clock_us(NULL) / 1000u;
}

static void stack_watermark_begin(void)
{
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    uint32_t current_sp = __get_MSP();
    volatile uint32_t *cursor = &__StackLimit;
    volatile uint32_t *limit = (volatile uint32_t *)current_sp;
    while (cursor < limit) {
        *cursor++ = OPENREF_STACK_PATTERN;
    }
    if (primask == 0u) {
        __enable_irq();
    }
}

static uint32_t stack_high_water_bytes(void)
{
    const volatile uint32_t *cursor = &__StackLimit;
    const volatile uint32_t *top = &__StackTop;
    while (cursor < top && *cursor == OPENREF_STACK_PATTERN) {
        cursor++;
    }
    return (uint32_t)((uintptr_t)top - (uintptr_t)cursor);
}

static bool timers_init(void)
{
    CLOCK_AttachClk(kMAIN_CLK_to_CTIMER0);
    CLOCK_AttachClk(kMAIN_CLK_to_CTIMER2);
    timing_clock_hz = CLOCK_GetCtimerClkFreq(0u);
    uint32_t pacing_clock_hz = CLOCK_GetCtimerClkFreq(2u);
    if (timing_clock_hz < OPENREF_TIMER_HZ ||
        pacing_clock_hz < OPENREF_TIMER_HZ ||
        timing_clock_hz % OPENREF_TIMER_HZ != 0u ||
        pacing_clock_hz % OPENREF_TIMER_HZ != 0u) {
        return false;
    }
    ctimer_config_t timing_config;
    CTIMER_GetDefaultConfig(&timing_config);
    timing_config.prescale = timing_clock_hz / OPENREF_TIMER_HZ - 1u;
    CTIMER_Init(CTIMER0, &timing_config);
    CTIMER_StartTimer(CTIMER0);

    ctimer_config_t pacing_config;
    CTIMER_GetDefaultConfig(&pacing_config);
    pacing_config.prescale = pacing_clock_hz / OPENREF_TIMER_HZ - 1u;
    CTIMER_Init(CTIMER2, &pacing_config);
    ctimer_match_config_t match = {
        .matchValue = OPENREF_PACING_TICKS,
        .enableCounterReset = true,
        .enableCounterStop = false,
        .outControl = kCTIMER_Output_NoAction,
        .outPinInitState = false,
        .enableInterrupt = true,
    };
    CTIMER_RegisterCallBack(CTIMER2, pacing_callbacks, kCTIMER_SingleCallback);
    CTIMER_SetupMatch(CTIMER2, kCTIMER_Match_0, &match);
    CTIMER_StartTimer(CTIMER2);
    return true;
}

static void print_result(const openref_audio_benchmark_result_t *result,
                         uint32_t pacing_ticks_consumed,
                         uint32_t pacing_overruns,
                         uint32_t elapsed_us)
{
    bool passed = result->passed && pacing_overruns == 0u;
    PRINTF("{\"schema\":\"openref-audio-benchmark-v1\","
        "\"benchmark_version\":1,\"target\":\"MIMXRT595-EVK-%s\","
        "\"execution_mode\":\"paced-target\",\"sample_rate_hz\":16000,"
        "\"channel_count\":1,\"sample_format\":\"signed-16-bit-pcm\","
        "\"frame_duration_us\":10000,\"codec_frame_bytes\":40,"
        "\"encoder_count\":1,\"decoder_count\":5,"
        "\"plc_period_packets\":97,\"warmup_blocks\":1000,"
        "\"processing_budget_us\":8000,\"clock_hz\":%u,"
        "\"silicon_revision\":\"CPUID-0x%08x\","
        "\"compiler\":\"GNU Arm %s\",\"optimization\":\"flash_release\","
        "\"codec\":\"NXP EtherMind MCUX SDK v26.06\","
        "\"firmware_commit\":\"%s\","
        "\"memory_placement\":\"MCUX generated flash_release linker map\","
        "\"clock_configuration\":\"BOARD_BootClockRUN core=%uHz; CTIMER input=%uHz; prescaled 1MHz\","
        "\"timer_source\":\"CTIMER0 32-bit free-running 1MHz MAIN_CLK; unsigned wrap\","
        "\"current_measurement\":\"%s\",\"requested_blocks\":%u,"
        "\"completed_blocks\":%u,\"plc_calls\":%u,"
        "\"encode_failures\":%u,\"decode_failures\":%u,"
        "\"process_failures\":%u,\"deadline_misses\":%u,"
        "\"maximum_encode_us\":%u,\"maximum_render_us\":%u,"
        "\"maximum_total_us\":%u,\"average_encode_us\":%u,"
        "\"average_render_us\":%u,\"average_total_us\":%u,"
        "\"stack_high_water_bytes\":%u,\"pacing_ticks\":%u,"
        "\"pacing_overruns\":%u,\"elapsed_us\":%u,"
        "\"idle_current_ma\":" STRINGIFY(OPENREF_IDLE_CURRENT_MA) ","
        "\"one_talker_current_ma\":" STRINGIFY(OPENREF_ONE_TALKER_CURRENT_MA) ","
        "\"six_talker_current_ma\":" STRINGIFY(OPENREF_SIX_TALKER_CURRENT_MA) ","
        "\"complete\":%s,\"passed\":%s}\r\n",
        STRINGIFY(OPENREF_BOARD_REVISION), (unsigned int)SystemCoreClock,
        (unsigned int)SCB->CPUID,
        __VERSION__, STRINGIFY(OPENREF_FIRMWARE_COMMIT),
        (unsigned int)SystemCoreClock, (unsigned int)timing_clock_hz,
        STRINGIFY(OPENREF_CURRENT_MEASUREMENT),
        (unsigned int)result->requested_blocks,
        (unsigned int)result->completed_blocks, (unsigned int)result->plc_calls,
        (unsigned int)result->encode_failures,
        (unsigned int)result->decode_failures,
        (unsigned int)result->process_failures,
        (unsigned int)result->deadline_misses,
        (unsigned int)result->maximum_encode_us,
        (unsigned int)result->maximum_render_us,
        (unsigned int)result->maximum_total_us,
        (unsigned int)result->average_encode_us,
        (unsigned int)result->average_render_us,
        (unsigned int)result->average_total_us,
        (unsigned int)stack_high_water_bytes(),
        (unsigned int)pacing_ticks_consumed, (unsigned int)pacing_overruns,
        (unsigned int)elapsed_us,
        result->complete ? "true" : "false", passed ? "true" : "false");
}

int main(void)
{
    BOARD_InitHardware();
    stack_watermark_begin();
    if (!timers_init() || !openref_rt595_lc3_init(&codec)) {
        PRINTF("OPENREF_RT595_BENCHMARK init=fail\r\n");
        for (;;) {
        }
    }
    openref_audio_benchmark_hooks_t hooks = {
        openref_rt595_lc3_encode, openref_rt595_lc3_decode,
        benchmark_clock_us, &codec, NULL};
    if (!openref_audio_benchmark_init(&benchmark, NULL, hooks)) {
        PRINTF("OPENREF_RT595_BENCHMARK benchmark_init=fail\r\n");
        for (;;) {
        }
    }
    const openref_watchdog_gate_config_t watchdog_config = {
        .required_mask = 1u,
        .startup_grace_ms = OPENREF_WATCHDOG_TASK_TIMEOUT_MS,
        .task_timeout_ms = {OPENREF_WATCHDOG_TASK_TIMEOUT_MS},
    };
    if (!openref_watchdog_gate_init(
            &watchdog_gate, &watchdog_config, benchmark_clock_ms()) ||
        !openref_rt595_watchdog_init(OPENREF_WATCHDOG_TIMEOUT_MS)) {
        PRINTF("OPENREF_RT595_BENCHMARK watchdog_init=fail\r\n");
        for (;;) {
        }
    }
    PRINTF("OPENREF_RT595_BENCHMARK start warmup=1000 measured=180000\r\n");
    const uint32_t total_blocks = OPENREF_AUDIO_BENCHMARK_DEFAULT_WARMUP_BLOCKS +
        OPENREF_AUDIO_BENCHMARK_DEFAULT_MEASURED_BLOCKS;
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    uint32_t consumed_tick = pacing_ticks;
    uint32_t workload_start_us = benchmark_clock_us(NULL);
    if (primask == 0u) {
        __enable_irq();
    }
    uint32_t pacing_ticks_consumed = 0u;
    uint32_t pacing_overruns = 0u;
    for (uint32_t block = 0u; block < total_blocks; block++) {
        while (pacing_ticks == consumed_tick) {
            __WFI();
        }
        uint32_t available_tick = pacing_ticks;
        if (available_tick - consumed_tick != 1u) {
            pacing_overruns += available_tick - consumed_tick - 1u;
        }
        consumed_tick = available_tick;
        pacing_ticks_consumed++;
        if (!openref_audio_benchmark_step(&benchmark)) {
            break;
        }
        uint64_t now_ms = benchmark_clock_ms();
        (void)openref_watchdog_gate_should_feed(&watchdog_gate, now_ms);
        if (watchdog_gate.last_fault_mask == 0u &&
            openref_watchdog_gate_report(&watchdog_gate, 0u, now_ms) &&
            openref_watchdog_gate_should_feed(&watchdog_gate, now_ms)) {
            openref_rt595_watchdog_feed();
        }
    }
    openref_audio_benchmark_result_t result;
    uint32_t elapsed_us = benchmark_clock_us(NULL) - workload_start_us;
    if (openref_audio_benchmark_get_result(&benchmark, &result)) {
        print_result(&result, pacing_ticks_consumed, pacing_overruns, elapsed_us);
    } else {
        PRINTF("OPENREF_RT595_BENCHMARK result=unavailable\r\n");
    }
    for (;;) {
        __WFI();
    }
}
