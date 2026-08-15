#include "openref_system_runtime.h"

#include <stddef.h>
#include <string.h>

bool openref_system_runtime_init(
    openref_system_runtime_t *runtime,
    const openref_startup_config_t *startup_config,
    openref_safety_gate_backend_t gate_backend,
    uint64_t now_ms)
{
    if (runtime == NULL) {
        return false;
    }
    memset(runtime, 0, sizeof(*runtime));
    if (!openref_startup_supervisor_init(
            &runtime->startup, startup_config, now_ms) ||
        !openref_safety_gate_driver_init(&runtime->gates, gate_backend)) {
        return false;
    }
    runtime->output = openref_safety_arbitrate(NULL);
    runtime->initialized = true;
    return true;
}

bool openref_system_runtime_tick(
    openref_system_runtime_t *runtime,
    const openref_startup_inputs_t *startup_inputs,
    const openref_safety_inputs_t *safety_inputs,
    uint64_t now_ms)
{
    if (runtime == NULL || !runtime->initialized || startup_inputs == NULL ||
        safety_inputs == NULL) {
        return false;
    }
    openref_safety_inputs_t combined = *safety_inputs;
    combined.startup_actions = openref_startup_supervisor_tick(
        &runtime->startup, startup_inputs, now_ms);
    combined.system_fault = combined.system_fault ||
        runtime->actuation_fault_latched;
    openref_safety_output_t desired = openref_safety_arbitrate(&combined);
    runtime->cycles++;
    if (!openref_safety_gate_driver_apply(&runtime->gates, &desired)) {
        runtime->actuation_fault_latched = true;
        runtime->actuation_faults++;
        combined.system_fault = true;
        runtime->output = openref_safety_arbitrate(&combined);
        return false;
    }
    runtime->output = desired;
    return true;
}
