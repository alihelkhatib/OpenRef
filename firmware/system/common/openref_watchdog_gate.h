#ifndef OPENREF_WATCHDOG_GATE_H
#define OPENREF_WATCHDOG_GATE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_WATCHDOG_MAX_TASKS 8u
#define OPENREF_WATCHDOG_CLOCK_FAULT (1u << 31)

typedef struct {
    uint8_t required_mask;
    uint32_t startup_grace_ms;
    uint32_t task_timeout_ms[OPENREF_WATCHDOG_MAX_TASKS];
} openref_watchdog_gate_config_t;

typedef struct {
    openref_watchdog_gate_config_t config;
    uint64_t started_ms;
    uint64_t last_evaluate_ms;
    uint64_t last_progress_ms[OPENREF_WATCHDOG_MAX_TASKS];
    uint8_t seen_mask;
    uint8_t progress_mask;
    uint32_t last_fault_mask;
    uint32_t feed_count;
    uint32_t fault_count;
    uint32_t invalid_report_count;
    bool healthy;
} openref_watchdog_gate_t;

bool openref_watchdog_gate_init(
    openref_watchdog_gate_t *gate,
    const openref_watchdog_gate_config_t *config,
    uint64_t now_ms);

bool openref_watchdog_gate_report(
    openref_watchdog_gate_t *gate,
    uint8_t task_index,
    uint64_t now_ms);

bool openref_watchdog_gate_should_feed(
    openref_watchdog_gate_t *gate,
    uint64_t now_ms);

#ifdef __cplusplus
}
#endif

#endif
