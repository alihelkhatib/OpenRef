#ifndef OPENREF_SYSTEM_RUNTIME_H
#define OPENREF_SYSTEM_RUNTIME_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_safety_arbiter.h"
#include "openref_safety_gate_driver.h"
#include "openref_startup_supervisor.h"

typedef struct {
    openref_startup_supervisor_t startup;
    openref_safety_gate_driver_t gates;
    openref_safety_output_t output;
    uint32_t cycles;
    uint32_t actuation_faults;
    bool actuation_fault_latched;
    bool initialized;
} openref_system_runtime_t;

bool openref_system_runtime_init(
    openref_system_runtime_t *runtime,
    const openref_startup_config_t *startup_config,
    openref_safety_gate_backend_t gate_backend,
    uint64_t now_ms);

bool openref_system_runtime_tick(
    openref_system_runtime_t *runtime,
    const openref_startup_inputs_t *startup_inputs,
    const openref_safety_inputs_t *safety_inputs,
    uint64_t now_ms);

#endif
