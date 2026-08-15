#include <assert.h>

#include "openref_status_policy.h"

static void test_readiness_and_independent_alerts(void)
{
    openref_status_policy_t policy;
    openref_status_policy_init(&policy);
    openref_status_inputs_t in = {.powered = true, .accessory_safe = true};
    openref_status_output_t out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_BOOTING && !out.operational_ready);
    in.connected = true;
    out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_CONNECTED && out.operational_ready);
    in.battery_low = true;
    out = openref_status_policy_update(&policy, &in);
    assert(out.operational_ready);
    assert((out.alerts & OPENREF_STATUS_ALERT_LOW_BATTERY) != 0u);
    in.link_degraded = true;
    out = openref_status_policy_update(&policy, &in);
    assert(!out.operational_ready);
    assert((out.attention_events & OPENREF_STATUS_ATTENTION_DEGRADED_LINK) != 0u);
    out = openref_status_policy_update(&policy, &in);
    assert((out.attention_events & OPENREF_STATUS_ATTENTION_DEGRADED_LINK) == 0u);
}

static void test_priority_and_critical_attention(void)
{
    openref_status_policy_t policy;
    openref_status_policy_init(&policy);
    openref_status_inputs_t in = {
        .powered = true, .connected = true, .battery_low = true,
        .battery_critical = true, .accessory_safe = true,
    };
    openref_status_output_t out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_CONNECTED);
    assert(!out.operational_ready);
    assert((out.attention_events &
            OPENREF_STATUS_ATTENTION_CRITICAL_BATTERY) != 0u);
    in.update_recovery = true;
    out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_UPDATE_RECOVERY);
    in.fault = true;
    out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_FAULT);
    assert((out.attention_events & OPENREF_STATUS_ATTENTION_FAULT) != 0u);
}

static void test_contradictions_fail_visible(void)
{
    openref_status_policy_t policy;
    openref_status_policy_init(&policy);
    openref_status_inputs_t in = {
        .powered = true, .forming = true, .connected = true,
        .accessory_safe = true,
    };
    openref_status_output_t out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_FAULT);
    assert(policy.inconsistent_input_count == 1u);
    in.forming = false;
    in.battery_critical = true;
    in.battery_low = false;
    out = openref_status_policy_update(&policy, &in);
    assert(out.mode == OPENREF_STATUS_FAULT);
    assert(policy.inconsistent_input_count == 2u);
}

int main(void)
{
    test_readiness_and_independent_alerts();
    test_priority_and_critical_attention();
    test_contradictions_fail_visible();
    return 0;
}
