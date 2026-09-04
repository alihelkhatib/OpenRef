#include "openref_watchdog_fg23.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static void increment_saturating(uint32_t *value)
{
    if (*value != UINT32_MAX) {
        (*value)++;
    }
}

static uint64_t clock_ms(openref_watchdog_fg23_t *watchdog)
{
    uint32_t current_us = watchdog->hooks.clock_us(watchdog->hooks.context);
    if (!watchdog->clock_initialized) {
        watchdog->previous_clock_us = current_us;
        watchdog->extended_clock_us = current_us;
        watchdog->clock_initialized = true;
        return watchdog->extended_clock_us / 1000u;
    }

    uint32_t delta_us = current_us - watchdog->previous_clock_us;
    if (current_us < watchdog->previous_clock_us && delta_us > INT32_MAX) {
        /* A small backwards step is a faulty clock, not 2^32-us wrap. */
        if (!watchdog->clock_fault_latched) {
            increment_saturating(&watchdog->clock_faults);
        }
        watchdog->clock_fault_latched = true;
        return watchdog->extended_clock_us == 0u
            ? 0u : watchdog->extended_clock_us / 1000u - 1u;
    }
    watchdog->previous_clock_us = current_us;
    watchdog->extended_clock_us += delta_us;
    return watchdog->extended_clock_us / 1000u;
}

bool openref_watchdog_fg23_init(
    openref_watchdog_fg23_t *watchdog,
    const openref_watchdog_fg23_config_t *config,
    openref_watchdog_fg23_hooks_t hooks)
{
    if (watchdog == NULL) {
        return false;
    }
    memset(watchdog, 0, sizeof(*watchdog));
    if (config == NULL || hooks.hardware_init == NULL ||
        hooks.hardware_feed == NULL || hooks.clock_us == NULL ||
        config->hardware_timeout_ms == 0u ||
        config->hardware_timeout_ms <= config->gate.startup_grace_ms) {
        return false;
    }
    for (uint8_t task = 0u; task < OPENREF_WATCHDOG_MAX_TASKS; task++) {
        if ((config->gate.required_mask & (uint8_t)(1u << task)) != 0u &&
            config->hardware_timeout_ms <= config->gate.task_timeout_ms[task]) {
            return false;
        }
    }
    watchdog->hooks = hooks;
    uint64_t now_ms = clock_ms(watchdog);
    if (!openref_watchdog_gate_init(&watchdog->gate, &config->gate, now_ms)) {
        return false;
    }
    if (!hooks.hardware_init(hooks.context, config->hardware_timeout_ms)) {
        return false;
    }
    watchdog->initialized = true;
    return true;
}

bool openref_watchdog_fg23_report(
    openref_watchdog_fg23_t *watchdog,
    uint8_t task_index)
{
    if (watchdog == NULL || !watchdog->initialized) {
        return false;
    }
    uint64_t now_ms = clock_ms(watchdog);
    return !watchdog->clock_fault_latched &&
        openref_watchdog_gate_report(&watchdog->gate, task_index, now_ms);
}

bool openref_watchdog_fg23_process(openref_watchdog_fg23_t *watchdog)
{
    if (watchdog == NULL || !watchdog->initialized) {
        return false;
    }
    uint64_t now_ms = clock_ms(watchdog);
    if (watchdog->clock_fault_latched ||
        !openref_watchdog_gate_should_feed(&watchdog->gate, now_ms)) {
        return false;
    }
    if (!watchdog->hooks.hardware_feed(watchdog->hooks.context)) {
        increment_saturating(&watchdog->hardware_feed_failures);
        return false;
    }
    return true;
}
