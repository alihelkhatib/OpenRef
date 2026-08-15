#include <assert.h>

#include "openref_charge_supervisor.h"

static openref_charge_supervisor_t make_supervisor(void)
{
    openref_charge_config_t config = {0, 450, 2800u, 4250u, 1000u};
    openref_charge_supervisor_t supervisor;
    assert(openref_charge_supervisor_init(&supervisor, &config, 0u));
    return supervisor;
}

static openref_charge_inputs_t valid_pack(void)
{
    openref_charge_inputs_t inputs = {
        .pack_present = true,
        .pack_identity_valid = true,
        .sensors_valid = true,
        .temperature_deci_c = 200,
        .pack_mv = 3700u,
    };
    return inputs;
}

static void test_precheck_charge_complete_and_removal(void)
{
    openref_charge_supervisor_t s = make_supervisor();
    openref_charge_inputs_t in = valid_pack();
    assert(openref_charge_supervisor_tick(&s, &in, 1u) ==
           OPENREF_CHARGE_PRECHECK);
    assert(!s.charge_enable);
    assert(openref_charge_supervisor_tick(&s, &in, 2u) ==
           OPENREF_CHARGE_ACTIVE);
    assert(s.charge_enable);
    in.charge_complete = true;
    assert(openref_charge_supervisor_tick(&s, &in, 3u) ==
           OPENREF_CHARGE_COMPLETE);
    assert(!s.charge_enable && s.completed_charges == 1u);
    in.pack_present = false;
    assert(openref_charge_supervisor_tick(&s, &in, 4u) ==
           OPENREF_CHARGE_EMPTY);
}

static void test_each_safety_fault_latches_until_removal(void)
{
    openref_charge_supervisor_t s = make_supervisor();
    openref_charge_inputs_t in = valid_pack();
    in.temperature_deci_c = 451;
    assert(openref_charge_supervisor_tick(&s, &in, 1u) ==
           OPENREF_CHARGE_FAULT);
    assert((s.fault_mask & OPENREF_CHARGE_FAULT_TEMPERATURE) != 0u);
    in.temperature_deci_c = 200;
    assert(openref_charge_supervisor_tick(&s, &in, 2u) ==
           OPENREF_CHARGE_FAULT);
    in.pack_present = false;
    assert(openref_charge_supervisor_tick(&s, &in, 3u) ==
           OPENREF_CHARGE_EMPTY);
    assert(s.fault_mask == 0u);

    s = make_supervisor();
    in = valid_pack();
    in.pack_identity_valid = false;
    openref_charge_supervisor_tick(&s, &in, 1u);
    assert((s.fault_mask & OPENREF_CHARGE_FAULT_PACK_ID) != 0u);
    s = make_supervisor();
    in = valid_pack();
    in.sensors_valid = false;
    openref_charge_supervisor_tick(&s, &in, 1u);
    assert((s.fault_mask & OPENREF_CHARGE_FAULT_SENSOR) != 0u);
    s = make_supervisor();
    in = valid_pack();
    in.pack_mv = 2700u;
    openref_charge_supervisor_tick(&s, &in, 1u);
    assert((s.fault_mask & OPENREF_CHARGE_FAULT_VOLTAGE) != 0u);
}

static void test_timeout_and_clock_fail_closed(void)
{
    openref_charge_supervisor_t s = make_supervisor();
    openref_charge_inputs_t in = valid_pack();
    openref_charge_supervisor_tick(&s, &in, 1u);
    openref_charge_supervisor_tick(&s, &in, 2u);
    assert(openref_charge_supervisor_tick(&s, &in, 1003u) ==
           OPENREF_CHARGE_FAULT);
    assert((s.fault_mask & OPENREF_CHARGE_FAULT_TIMEOUT) != 0u);
    s = make_supervisor();
    assert(openref_charge_supervisor_tick(&s, &in, 1u) ==
           OPENREF_CHARGE_PRECHECK);
    assert(openref_charge_supervisor_tick(&s, &in, 0u) ==
           OPENREF_CHARGE_FAULT);
    assert((s.fault_mask & OPENREF_CHARGE_FAULT_CLOCK) != 0u);
}

int main(void)
{
    test_precheck_charge_complete_and_removal();
    test_each_safety_fault_latches_until_removal();
    test_timeout_and_clock_fail_closed();
    return 0;
}
