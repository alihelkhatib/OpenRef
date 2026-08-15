#ifndef OPENREF_STARTUP_SUPERVISOR_H
#define OPENREF_STARTUP_SUPERVISOR_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_STARTUP_SAFE = 0,
    OPENREF_STARTUP_POWER_WAIT,
    OPENREF_STARTUP_PROCESSOR_WAIT,
    OPENREF_STARTUP_LOCAL_READY,
    OPENREF_STARTUP_OPERATIONAL,
    OPENREF_STARTUP_FAULT
} openref_startup_state_t;

#define OPENREF_STARTUP_ACTION_ENABLE_RAILS (1u << 0)
#define OPENREF_STARTUP_ACTION_RELEASE_RESETS (1u << 1)
#define OPENREF_STARTUP_ACTION_MUTE_AUDIO (1u << 2)
#define OPENREF_STARTUP_ACTION_PERMIT_RF_TX (1u << 3)
#define OPENREF_STARTUP_ACTION_REPORT_READY (1u << 4)
#define OPENREF_STARTUP_ACTION_REPORT_FAULT (1u << 5)

#define OPENREF_STARTUP_FAULT_RAIL_TIMEOUT (1u << 0)
#define OPENREF_STARTUP_FAULT_PROCESSOR_TIMEOUT (1u << 1)
#define OPENREF_STARTUP_FAULT_RUNTIME_INTERLOCK (1u << 2)
#define OPENREF_STARTUP_FAULT_CLOCK (1u << 3)

typedef struct {
    uint32_t rail_timeout_ms;
    uint32_t processor_timeout_ms;
} openref_startup_config_t;

typedef struct {
    bool power_safe;
    bool rails_good;
    bool authenticated_boot;
    bool configuration_valid;
    bool accessory_safe;
    bool peer_healthy;
    bool crew_session_valid;
} openref_startup_inputs_t;

typedef struct {
    openref_startup_config_t config;
    openref_startup_state_t state;
    uint64_t state_since_ms;
    uint64_t last_tick_ms;
    uint32_t fault_mask;
    uint32_t transition_count;
} openref_startup_supervisor_t;

bool openref_startup_supervisor_init(
    openref_startup_supervisor_t *supervisor,
    const openref_startup_config_t *config,
    uint64_t now_ms);

uint32_t openref_startup_supervisor_tick(
    openref_startup_supervisor_t *supervisor,
    const openref_startup_inputs_t *inputs,
    uint64_t now_ms);

#endif
