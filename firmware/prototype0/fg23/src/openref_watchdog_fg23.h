#ifndef OPENREF_WATCHDOG_FG23_H
#define OPENREF_WATCHDOG_FG23_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_watchdog_driver.h"

typedef struct {
    uint32_t requested_timeout_ms;
    uint32_t effective_timeout_ms;
    uint8_t period_selector;
    bool configured;
} openref_watchdog_fg23_t;

typedef struct {
    uint32_t previous_us;
    uint64_t epoch_us;
    bool initialized;
} openref_watchdog_fg23_clock_t;

bool openref_watchdog_fg23_select_period(
    uint32_t requested_timeout_ms,
    uint8_t *period_selector,
    uint32_t *effective_timeout_ms);

bool openref_watchdog_fg23_configure(void *context, uint32_t timeout_ms);
bool openref_watchdog_fg23_feed(void *context);

uint64_t openref_watchdog_fg23_monotonic_ms(
    openref_watchdog_fg23_clock_t *clock,
    uint32_t raw_time_us);

openref_watchdog_backend_t openref_watchdog_fg23_backend(
    openref_watchdog_fg23_t *context);

#endif
