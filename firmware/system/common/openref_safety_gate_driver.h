#ifndef OPENREF_SAFETY_GATE_DRIVER_H
#define OPENREF_SAFETY_GATE_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_safety_arbiter.h"

typedef bool (*openref_safety_set_gate_fn)(void *context, bool enabled);

typedef struct {
    openref_safety_set_gate_fn set_voice_uplink;
    openref_safety_set_gate_fn set_playback;
    openref_safety_set_gate_fn set_network_control_tx;
    void *context;
} openref_safety_gate_backend_t;

typedef struct {
    openref_safety_gate_backend_t backend;
    openref_safety_output_t applied;
    uint32_t transitions;
    uint32_t failures;
    bool initialized;
} openref_safety_gate_driver_t;

bool openref_safety_gate_driver_init(
    openref_safety_gate_driver_t *driver,
    openref_safety_gate_backend_t backend);

bool openref_safety_gate_driver_apply(
    openref_safety_gate_driver_t *driver,
    const openref_safety_output_t *desired);

#endif
