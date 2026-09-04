#ifndef OPENREF_SAFETY_OUTPUT_GATE_H
#define OPENREF_SAFETY_OUTPUT_GATE_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_safety_arbiter.h"

/*
 * The callback must synchronously drive (or verify) the requested hardware
 * state. Returning false latches the gate and triggers a best-effort shutdown
 * of every output; it must not merely mean that an asynchronous request was
 * queued.
 */
typedef bool (*openref_safety_output_set_fn)(void *context, bool enabled);

typedef struct {
    openref_safety_output_set_fn set_voice_uplink;
    openref_safety_output_set_fn set_playback;
    openref_safety_output_set_fn set_network_control_tx;
    void *context;
} openref_safety_output_hooks_t;

typedef struct {
    openref_safety_output_hooks_t hooks;
    openref_safety_output_t applied;
    /* Saturating counts of valid apply attempts and failed init/apply calls. */
    uint32_t apply_count;
    uint32_t failure_count;
    bool initialized;
    bool fault_latched;
} openref_safety_output_gate_t;

bool openref_safety_output_gate_init(
    openref_safety_output_gate_t *gate,
    openref_safety_output_hooks_t hooks);

bool openref_safety_output_gate_apply(
    openref_safety_output_gate_t *gate,
    const openref_safety_output_t *requested);

#endif
