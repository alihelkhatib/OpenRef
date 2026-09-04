#include <assert.h>
#include <stdint.h>

#include "openref_watchdog_gate.h"

static openref_watchdog_gate_t make_gate(void)
{
    openref_watchdog_gate_config_t config = {
        .required_mask = 0x07u,
        .startup_grace_ms = 100u,
        .task_timeout_ms = {50u, 60u, 70u},
    };
    openref_watchdog_gate_t gate;
    assert(openref_watchdog_gate_init(&gate, &config, 1000u));
    return gate;
}

static void test_requires_fresh_progress_from_every_task(void)
{
    openref_watchdog_gate_t gate = make_gate();
    assert(openref_watchdog_gate_report(&gate, 0u, 1010u));
    assert(openref_watchdog_gate_report(&gate, 1u, 1011u));
    assert(!openref_watchdog_gate_should_feed(&gate, 1012u));
    assert(openref_watchdog_gate_report(&gate, 2u, 1013u));
    assert(openref_watchdog_gate_should_feed(&gate, 1014u));
    assert(gate.feed_count == 1u);
    assert(!openref_watchdog_gate_should_feed(&gate, 1015u));
    assert(openref_watchdog_gate_report(&gate, 0u, 1020u));
    assert(openref_watchdog_gate_report(&gate, 1u, 1020u));
    assert(openref_watchdog_gate_report(&gate, 2u, 1020u));
    assert(openref_watchdog_gate_should_feed(&gate, 1021u));
}

static void test_stale_missing_and_clock_faults_fail_closed(void)
{
    openref_watchdog_gate_t gate = make_gate();
    assert(!openref_watchdog_gate_should_feed(&gate, 1101u));
    assert(gate.last_fault_mask == 0x07u);
    assert(gate.fault_count == 1u);
    assert(openref_watchdog_gate_report(&gate, 0u, 1110u));
    assert(openref_watchdog_gate_report(&gate, 1u, 1110u));
    assert(openref_watchdog_gate_report(&gate, 2u, 1110u));
    assert(openref_watchdog_gate_should_feed(&gate, 1111u));
    assert(!openref_watchdog_gate_should_feed(&gate, 1182u));
    assert(gate.last_fault_mask == 0x07u);
    assert(!openref_watchdog_gate_should_feed(&gate, 1181u));
    assert(gate.last_fault_mask == OPENREF_WATCHDOG_CLOCK_FAULT);
}

static void test_rejects_invalid_reports_and_configuration(void)
{
    openref_watchdog_gate_t gate = make_gate();
    assert(!openref_watchdog_gate_report(&gate, 7u, 1001u));
    assert(gate.invalid_report_count == 1u);
    assert(openref_watchdog_gate_report(&gate, 0u, 1005u));
    assert(!openref_watchdog_gate_report(&gate, 0u, 1004u));
    openref_watchdog_gate_config_t invalid = {.required_mask = 1u};
    assert(!openref_watchdog_gate_init(&gate, &invalid, 0u));
}

static void test_diagnostic_counters_saturate(void)
{
    openref_watchdog_gate_t gate = make_gate();
    gate.invalid_report_count = UINT32_MAX;
    assert(!openref_watchdog_gate_report(&gate, 7u, 1001u));
    assert(gate.invalid_report_count == UINT32_MAX);

    gate.fault_count = UINT32_MAX;
    assert(!openref_watchdog_gate_should_feed(&gate, 1101u));
    assert(gate.fault_count == UINT32_MAX);

    gate = make_gate();
    gate.feed_count = UINT32_MAX;
    assert(openref_watchdog_gate_report(&gate, 0u, 1010u));
    assert(openref_watchdog_gate_report(&gate, 1u, 1010u));
    assert(openref_watchdog_gate_report(&gate, 2u, 1010u));
    assert(openref_watchdog_gate_should_feed(&gate, 1011u));
    assert(gate.feed_count == UINT32_MAX);
}

int main(void)
{
    test_requires_fresh_progress_from_every_task();
    test_stale_missing_and_clock_faults_fail_closed();
    test_rejects_invalid_reports_and_configuration();
    test_diagnostic_counters_saturate();
    return 0;
}
