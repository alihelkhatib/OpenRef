#include <assert.h>
#include <stdint.h>
#include <stddef.h>

#include "openref_safety_output_gate.h"

typedef struct {
    char events[32];
    uint8_t count;
    char fail_event;
} fake_target_t;

static bool record(fake_target_t *target, char event)
{
    target->events[target->count++] = event;
    return target->fail_event != event;
}

static bool voice(void *context, bool enabled)
{
    return record(context, enabled ? 'V' : 'v');
}

static bool playback(void *context, bool enabled)
{
    return record(context, enabled ? 'P' : 'p');
}

static bool radio(void *context, bool enabled)
{
    return record(context, enabled ? 'R' : 'r');
}

static openref_safety_output_hooks_t hooks(fake_target_t *target)
{
    openref_safety_output_hooks_t result = {voice, playback, radio, target};
    return result;
}

static void test_safe_start_and_ordered_enable_disable(void)
{
    fake_target_t target = {0};
    openref_safety_output_gate_t gate;
    assert(openref_safety_output_gate_init(&gate, hooks(&target)));
    assert(target.count == 3u);
    assert(target.events[0] == 'v' && target.events[1] == 'p' &&
           target.events[2] == 'r');

    openref_safety_output_t enabled = {
        .voice_uplink_enabled = true,
        .playback_enabled = true,
        .network_control_tx_enabled = true,
    };
    assert(openref_safety_output_gate_apply(&gate, &enabled));
    assert(target.events[3] == 'R' && target.events[4] == 'P' &&
           target.events[5] == 'V');

    openref_safety_output_t disabled = {0};
    assert(openref_safety_output_gate_apply(&gate, &disabled));
    assert(target.events[6] == 'v' && target.events[7] == 'p' &&
           target.events[8] == 'r');
}

static void test_callback_failure_latches_safe_state(void)
{
    fake_target_t target = {.fail_event = 'P'};
    openref_safety_output_gate_t gate;
    assert(openref_safety_output_gate_init(&gate, hooks(&target)));
    openref_safety_output_t enabled = {
        .voice_uplink_enabled = true,
        .playback_enabled = true,
        .network_control_tx_enabled = true,
    };
    assert(!openref_safety_output_gate_apply(&gate, &enabled));
    assert(gate.fault_latched && gate.failure_count == 1u);
    assert(gate.apply_count == 1u);
    assert(!gate.applied.voice_uplink_enabled && !gate.applied.playback_enabled &&
           !gate.applied.network_control_tx_enabled);
    assert(target.events[target.count - 3u] == 'v');
    assert(target.events[target.count - 2u] == 'p');
    assert(target.events[target.count - 1u] == 'r');
    assert(!openref_safety_output_gate_apply(&gate, &enabled));
    assert(gate.apply_count == 1u && gate.failure_count == 1u);
}

static void test_failure_does_not_grant_later_permissions(void)
{
    fake_target_t target = {.fail_event = 'R'};
    openref_safety_output_gate_t gate;
    assert(openref_safety_output_gate_init(&gate, hooks(&target)));
    openref_safety_output_t enabled = {
        .voice_uplink_enabled = true,
        .playback_enabled = true,
        .network_control_tx_enabled = true,
    };

    assert(!openref_safety_output_gate_apply(&gate, &enabled));
    /* Failed radio enable is followed immediately by the safe-state sequence. */
    assert(target.count == 7u);
    assert(target.events[3] == 'R');
    assert(target.events[4] == 'v');
    assert(target.events[5] == 'p');
    assert(target.events[6] == 'r');
}

static void test_failed_reinitialization_clears_live_gate(void)
{
    fake_target_t target = {0};
    openref_safety_output_gate_t gate;
    assert(openref_safety_output_gate_init(&gate, hooks(&target)));

    openref_safety_output_hooks_t invalid = hooks(&target);
    invalid.set_playback = NULL;
    assert(!openref_safety_output_gate_init(&gate, invalid));
    assert(!gate.initialized && !gate.fault_latched);

    openref_safety_output_t disabled = {0};
    assert(!openref_safety_output_gate_apply(&gate, &disabled));
}

static void test_initial_safe_state_failure_is_not_initialized(void)
{
    fake_target_t target = {.fail_event = 'v'};
    openref_safety_output_gate_t gate;
    assert(!openref_safety_output_gate_init(&gate, hooks(&target)));
    assert(!gate.initialized && gate.fault_latched);
    assert(gate.failure_count == 1u && gate.apply_count == 0u);
    /* Safe initialization is best effort: all three outputs are attempted. */
    assert(target.count == 3u);
}

static void test_diagnostic_counters_saturate(void)
{
    fake_target_t target = {0};
    openref_safety_output_gate_t gate;
    assert(openref_safety_output_gate_init(&gate, hooks(&target)));
    openref_safety_output_t disabled = {0};

    gate.apply_count = UINT32_MAX;
    assert(openref_safety_output_gate_apply(&gate, &disabled));
    assert(gate.apply_count == UINT32_MAX);

    gate.failure_count = UINT32_MAX;
    target.fail_event = 'R';
    openref_safety_output_t radio_enabled = {
        .network_control_tx_enabled = true,
    };
    assert(!openref_safety_output_gate_apply(&gate, &radio_enabled));
    assert(gate.apply_count == UINT32_MAX);
    assert(gate.failure_count == UINT32_MAX);
}

static void test_invalid_hooks_fail_closed(void)
{
    fake_target_t target = {0};
    openref_safety_output_gate_t gate;
    openref_safety_output_hooks_t invalid = hooks(&target);
    invalid.set_voice_uplink = NULL;
    assert(!openref_safety_output_gate_init(&gate, invalid));
    assert(!openref_safety_output_gate_apply(NULL, NULL));
}

int main(void)
{
    test_safe_start_and_ordered_enable_disable();
    test_callback_failure_latches_safe_state();
    test_failure_does_not_grant_later_permissions();
    test_failed_reinitialization_clears_live_gate();
    test_initial_safe_state_failure_is_not_initialized();
    test_diagnostic_counters_saturate();
    test_invalid_hooks_fail_closed();
    return 0;
}
