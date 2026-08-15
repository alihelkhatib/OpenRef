#include <assert.h>

#include "openref_startup_supervisor.h"

static openref_startup_supervisor_t make_supervisor(void)
{
    openref_startup_config_t config = {100u, 200u};
    openref_startup_supervisor_t supervisor;
    assert(openref_startup_supervisor_init(&supervisor, &config, 0u));
    return supervisor;
}

static void test_safe_order_and_session_gating(void)
{
    openref_startup_supervisor_t s = make_supervisor();
    openref_startup_inputs_t in = {0};
    assert(openref_startup_supervisor_tick(&s, &in, 1u) ==
           OPENREF_STARTUP_ACTION_MUTE_AUDIO);
    in.power_safe = true;
    uint32_t action = openref_startup_supervisor_tick(&s, &in, 2u);
    assert((action & OPENREF_STARTUP_ACTION_ENABLE_RAILS) != 0u);
    assert((action & OPENREF_STARTUP_ACTION_RELEASE_RESETS) == 0u);
    in.rails_good = true;
    action = openref_startup_supervisor_tick(&s, &in, 3u);
    assert((action & OPENREF_STARTUP_ACTION_RELEASE_RESETS) != 0u);
    in.authenticated_boot = true;
    in.configuration_valid = true;
    in.accessory_safe = true;
    in.peer_healthy = true;
    action = openref_startup_supervisor_tick(&s, &in, 4u);
    assert(s.state == OPENREF_STARTUP_LOCAL_READY);
    assert((action & OPENREF_STARTUP_ACTION_PERMIT_RF_TX) == 0u);
    in.crew_session_valid = true;
    action = openref_startup_supervisor_tick(&s, &in, 5u);
    assert(s.state == OPENREF_STARTUP_OPERATIONAL);
    assert((action & OPENREF_STARTUP_ACTION_MUTE_AUDIO) == 0u);
    assert((action & OPENREF_STARTUP_ACTION_PERMIT_RF_TX) != 0u);
    in.crew_session_valid = false;
    action = openref_startup_supervisor_tick(&s, &in, 6u);
    assert(s.state == OPENREF_STARTUP_LOCAL_READY);
    assert((action & OPENREF_STARTUP_ACTION_MUTE_AUDIO) != 0u);
}

static void test_timeouts_power_loss_and_clock_fault(void)
{
    openref_startup_supervisor_t s = make_supervisor();
    openref_startup_inputs_t in = {.power_safe = true};
    openref_startup_supervisor_tick(&s, &in, 1u);
    uint32_t action = openref_startup_supervisor_tick(&s, &in, 102u);
    assert(s.state == OPENREF_STARTUP_FAULT);
    assert((action & OPENREF_STARTUP_ACTION_REPORT_FAULT) != 0u);
    assert((action & OPENREF_STARTUP_ACTION_ENABLE_RAILS) == 0u);
    in.power_safe = false;
    assert(openref_startup_supervisor_tick(&s, &in, 103u) ==
           OPENREF_STARTUP_ACTION_MUTE_AUDIO);
    assert(s.state == OPENREF_STARTUP_SAFE);
    action = openref_startup_supervisor_tick(&s, &in, 102u);
    assert((s.fault_mask & OPENREF_STARTUP_FAULT_CLOCK) != 0u);
    assert((action & OPENREF_STARTUP_ACTION_REPORT_FAULT) != 0u);
}

static void test_processor_timeout(void)
{
    openref_startup_supervisor_t s = make_supervisor();
    openref_startup_inputs_t in = {.power_safe = true};
    openref_startup_supervisor_tick(&s, &in, 1u);
    in.rails_good = true;
    openref_startup_supervisor_tick(&s, &in, 2u);
    openref_startup_supervisor_tick(&s, &in, 203u);
    assert((s.fault_mask & OPENREF_STARTUP_FAULT_PROCESSOR_TIMEOUT) != 0u);
}

int main(void)
{
    test_safe_order_and_session_gating();
    test_timeouts_power_loss_and_clock_fault();
    test_processor_timeout();
    return 0;
}
