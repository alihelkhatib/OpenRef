#include "openref_safety_output_gate.h"

#include <limits.h>
#include <stddef.h>

static void increment_saturating(uint32_t *value)
{
    if (*value != UINT32_MAX) {
        (*value)++;
    }
}

static bool force_safe(openref_safety_output_gate_t *gate)
{
    bool voice_safe = gate->hooks.set_voice_uplink(gate->hooks.context, false);
    bool playback_safe = gate->hooks.set_playback(gate->hooks.context, false);
    bool radio_safe = gate->hooks.set_network_control_tx(gate->hooks.context, false);
    gate->applied = (openref_safety_output_t){0};
    return voice_safe && playback_safe && radio_safe;
}

static bool latch_failure(openref_safety_output_gate_t *gate)
{
    increment_saturating(&gate->failure_count);
    gate->fault_latched = true;
    (void)force_safe(gate);
    return false;
}

bool openref_safety_output_gate_init(
    openref_safety_output_gate_t *gate,
    openref_safety_output_hooks_t hooks)
{
    if (gate == NULL) {
        return false;
    }

    /* A failed reinitialization must not leave a previously usable gate live. */
    *gate = (openref_safety_output_gate_t){0};
    if (hooks.set_voice_uplink == NULL ||
        hooks.set_playback == NULL || hooks.set_network_control_tx == NULL) {
        return false;
    }
    gate->hooks = hooks;
    if (!force_safe(gate)) {
        gate->fault_latched = true;
        gate->failure_count = 1u;
        return false;
    }
    gate->initialized = true;
    return true;
}

bool openref_safety_output_gate_apply(
    openref_safety_output_gate_t *gate,
    const openref_safety_output_t *requested)
{
    if (gate == NULL || !gate->initialized || requested == NULL ||
        gate->fault_latched) {
        return false;
    }

    /* Remove permissions before adding any. Voice always closes first. */
    if (gate->applied.voice_uplink_enabled && !requested->voice_uplink_enabled) {
        if (!gate->hooks.set_voice_uplink(gate->hooks.context, false)) {
            increment_saturating(&gate->apply_count);
            return latch_failure(gate);
        }
    }
    if (gate->applied.playback_enabled && !requested->playback_enabled) {
        if (!gate->hooks.set_playback(gate->hooks.context, false)) {
            increment_saturating(&gate->apply_count);
            return latch_failure(gate);
        }
    }
    if (gate->applied.network_control_tx_enabled &&
        !requested->network_control_tx_enabled) {
        if (!gate->hooks.set_network_control_tx(gate->hooks.context, false)) {
            increment_saturating(&gate->apply_count);
            return latch_failure(gate);
        }
    }

    /* Establish the transport permission before playback and captured voice. */
    if (!gate->applied.network_control_tx_enabled &&
        requested->network_control_tx_enabled) {
        if (!gate->hooks.set_network_control_tx(gate->hooks.context, true)) {
            increment_saturating(&gate->apply_count);
            return latch_failure(gate);
        }
    }
    if (!gate->applied.playback_enabled && requested->playback_enabled) {
        if (!gate->hooks.set_playback(gate->hooks.context, true)) {
            increment_saturating(&gate->apply_count);
            return latch_failure(gate);
        }
    }
    if (!gate->applied.voice_uplink_enabled && requested->voice_uplink_enabled) {
        if (!gate->hooks.set_voice_uplink(gate->hooks.context, true)) {
            increment_saturating(&gate->apply_count);
            return latch_failure(gate);
        }
    }

    increment_saturating(&gate->apply_count);
    gate->applied = *requested;
    return true;
}
