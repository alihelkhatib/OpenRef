#include "openref_watchdog_driver.h"

#include <stddef.h>
#include <string.h>

bool openref_watchdog_driver_init(
    openref_watchdog_driver_t *driver,
    const openref_watchdog_gate_config_t *gate_config,
    openref_watchdog_backend_t backend,
    uint32_t hardware_timeout_ms,
    uint64_t now_ms)
{
    if (driver == NULL || gate_config == NULL || backend.configure == NULL ||
        backend.feed == NULL || hardware_timeout_ms == 0u) {
        return false;
    }
    memset(driver, 0, sizeof(*driver));
    driver->backend = backend;
    driver->hardware_timeout_ms = hardware_timeout_ms;
    if (!openref_watchdog_gate_init(&driver->gate, gate_config, now_ms)) {
        return false;
    }
    if (!backend.configure(backend.context, hardware_timeout_ms)) {
        driver->backend_failure_count = 1u;
        driver->fault_latched = true;
        return false;
    }
    driver->initialized = true;
    return true;
}

bool openref_watchdog_driver_report(
    openref_watchdog_driver_t *driver,
    uint8_t task_index,
    uint64_t now_ms)
{
    if (driver == NULL || !driver->initialized || driver->fault_latched) {
        return false;
    }
    return openref_watchdog_gate_report(&driver->gate, task_index, now_ms);
}

bool openref_watchdog_driver_tick(
    openref_watchdog_driver_t *driver,
    uint64_t now_ms)
{
    if (driver == NULL || !driver->initialized || driver->fault_latched) {
        return false;
    }
    if (!openref_watchdog_gate_should_feed(&driver->gate, now_ms)) {
        driver->withheld_count++;
        return false;
    }
    if (!driver->backend.feed(driver->backend.context)) {
        driver->backend_failure_count++;
        driver->fault_latched = true;
        return false;
    }
    driver->hardware_feed_count++;
    return true;
}
