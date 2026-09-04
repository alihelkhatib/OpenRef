#ifndef OPENREF_WATCHDOG_FG23_H
#define OPENREF_WATCHDOG_FG23_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_watchdog_gate.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef bool (*openref_watchdog_fg23_hardware_init_fn)(
    void *context, uint32_t minimum_timeout_ms);
typedef bool (*openref_watchdog_fg23_hardware_feed_fn)(void *context);
typedef uint32_t (*openref_watchdog_fg23_clock_us_fn)(void *context);

typedef struct {
    openref_watchdog_fg23_hardware_init_fn hardware_init;
    openref_watchdog_fg23_hardware_feed_fn hardware_feed;
    openref_watchdog_fg23_clock_us_fn clock_us;
    void *context;
} openref_watchdog_fg23_hooks_t;

typedef struct {
    openref_watchdog_gate_config_t gate;
    uint32_t hardware_timeout_ms;
} openref_watchdog_fg23_config_t;

typedef struct {
    openref_watchdog_gate_t gate;
    openref_watchdog_fg23_hooks_t hooks;
    uint32_t previous_clock_us;
    uint64_t extended_clock_us;
    uint32_t hardware_feed_failures;
    uint32_t clock_faults;
    bool initialized;
    bool clock_initialized;
    bool clock_fault_latched;
} openref_watchdog_fg23_t;

bool openref_watchdog_fg23_init(
    openref_watchdog_fg23_t *watchdog,
    const openref_watchdog_fg23_config_t *config,
    openref_watchdog_fg23_hooks_t hooks);

bool openref_watchdog_fg23_report(
    openref_watchdog_fg23_t *watchdog,
    uint8_t task_index);

/* Evaluate task progress and feed WDOG0 only when the portable gate permits. */
bool openref_watchdog_fg23_process(openref_watchdog_fg23_t *watchdog);

#ifdef __cplusplus
}
#endif

#endif
