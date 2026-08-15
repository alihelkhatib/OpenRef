#ifndef OPENREF_WATCHDOG_DRIVER_H
#define OPENREF_WATCHDOG_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_watchdog_gate.h"

typedef bool (*openref_watchdog_configure_fn)(void *context, uint32_t timeout_ms);
typedef bool (*openref_watchdog_feed_fn)(void *context);

typedef struct {
    openref_watchdog_configure_fn configure;
    openref_watchdog_feed_fn feed;
    void *context;
} openref_watchdog_backend_t;

typedef struct {
    openref_watchdog_gate_t gate;
    openref_watchdog_backend_t backend;
    uint32_t hardware_timeout_ms;
    uint32_t hardware_feed_count;
    uint32_t withheld_count;
    uint32_t backend_failure_count;
    bool fault_latched;
    bool initialized;
} openref_watchdog_driver_t;

bool openref_watchdog_driver_init(
    openref_watchdog_driver_t *driver,
    const openref_watchdog_gate_config_t *gate_config,
    openref_watchdog_backend_t backend,
    uint32_t hardware_timeout_ms,
    uint64_t now_ms);

bool openref_watchdog_driver_report(
    openref_watchdog_driver_t *driver,
    uint8_t task_index,
    uint64_t now_ms);

bool openref_watchdog_driver_tick(
    openref_watchdog_driver_t *driver,
    uint64_t now_ms);

#endif
