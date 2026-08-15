#include "openref_watchdog_gate.h"

#include <stddef.h>
#include <string.h>

bool openref_watchdog_gate_init(
    openref_watchdog_gate_t *gate,
    const openref_watchdog_gate_config_t *config,
    uint64_t now_ms)
{
    if (gate == NULL || config == NULL || config->required_mask == 0u) {
        return false;
    }
    for (uint8_t task = 0u; task < OPENREF_WATCHDOG_MAX_TASKS; task++) {
        if ((config->required_mask & (uint8_t)(1u << task)) != 0u &&
            config->task_timeout_ms[task] == 0u) {
            return false;
        }
    }
    memset(gate, 0, sizeof(*gate));
    gate->config = *config;
    gate->started_ms = now_ms;
    gate->last_evaluate_ms = now_ms;
    return true;
}

bool openref_watchdog_gate_report(
    openref_watchdog_gate_t *gate,
    uint8_t task_index,
    uint64_t now_ms)
{
    if (gate == NULL || task_index >= OPENREF_WATCHDOG_MAX_TASKS ||
        (gate->config.required_mask & (uint8_t)(1u << task_index)) == 0u ||
        ((gate->seen_mask & (uint8_t)(1u << task_index)) != 0u &&
         now_ms < gate->last_progress_ms[task_index])) {
        if (gate != NULL) {
            gate->invalid_report_count++;
        }
        return false;
    }
    uint8_t bit = (uint8_t)(1u << task_index);
    gate->last_progress_ms[task_index] = now_ms;
    gate->seen_mask |= bit;
    gate->progress_mask |= bit;
    return true;
}

bool openref_watchdog_gate_should_feed(
    openref_watchdog_gate_t *gate,
    uint64_t now_ms)
{
    if (gate == NULL) {
        return false;
    }
    uint32_t fault_mask = 0u;
    if (now_ms < gate->last_evaluate_ms || now_ms < gate->started_ms) {
        fault_mask = OPENREF_WATCHDOG_CLOCK_FAULT;
    } else {
        gate->last_evaluate_ms = now_ms;
        for (uint8_t task = 0u; task < OPENREF_WATCHDOG_MAX_TASKS; task++) {
            uint8_t bit = (uint8_t)(1u << task);
            if ((gate->config.required_mask & bit) == 0u) {
                continue;
            }
            bool missing_after_grace = (gate->seen_mask & bit) == 0u &&
                now_ms - gate->started_ms > gate->config.startup_grace_ms;
            bool stale = (gate->seen_mask & bit) != 0u &&
                now_ms - gate->last_progress_ms[task] >
                    gate->config.task_timeout_ms[task];
            if (missing_after_grace || stale) {
                fault_mask |= bit;
            }
        }
    }
    if (fault_mask != 0u) {
        if (gate->healthy || gate->last_fault_mask != fault_mask) {
            gate->fault_count++;
        }
        gate->healthy = false;
        gate->last_fault_mask = fault_mask;
        return false;
    }
    if ((gate->progress_mask & gate->config.required_mask) !=
        gate->config.required_mask) {
        return false;
    }
    gate->progress_mask &= (uint8_t)~gate->config.required_mask;
    gate->last_fault_mask = 0u;
    gate->healthy = true;
    gate->feed_count++;
    return true;
}
