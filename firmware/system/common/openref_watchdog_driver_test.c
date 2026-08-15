#include <assert.h>
#include <string.h>

#include "openref_watchdog_driver.h"

typedef struct {
    uint32_t configured_timeout_ms;
    uint32_t feeds;
    bool configure_ok;
    bool feed_ok;
} fake_backend_t;

static bool configure(void *context, uint32_t timeout_ms)
{
    fake_backend_t *backend = context;
    backend->configured_timeout_ms = timeout_ms;
    return backend->configure_ok;
}

static bool feed(void *context)
{
    fake_backend_t *backend = context;
    backend->feeds++;
    return backend->feed_ok;
}

static openref_watchdog_gate_config_t config(void)
{
    openref_watchdog_gate_config_t value;
    memset(&value, 0, sizeof(value));
    value.required_mask = 0x03u;
    value.startup_grace_ms = 100u;
    value.task_timeout_ms[0] = 50u;
    value.task_timeout_ms[1] = 50u;
    return value;
}

static void test_feeds_only_after_all_tasks_progress(void)
{
    fake_backend_t backend = {0u, 0u, true, true};
    openref_watchdog_backend_t hooks = {configure, feed, &backend};
    openref_watchdog_gate_config_t gate_config = config();
    openref_watchdog_driver_t driver;
    assert(openref_watchdog_driver_init(&driver, &gate_config, hooks, 250u, 0u));
    assert(backend.configured_timeout_ms == 250u);
    assert(!openref_watchdog_driver_tick(&driver, 10u));
    assert(openref_watchdog_driver_report(&driver, 0u, 20u));
    assert(!openref_watchdog_driver_tick(&driver, 20u));
    assert(openref_watchdog_driver_report(&driver, 1u, 25u));
    assert(openref_watchdog_driver_tick(&driver, 25u));
    assert(backend.feeds == 1u && driver.hardware_feed_count == 1u);
    assert(!openref_watchdog_driver_tick(&driver, 30u));
    assert(backend.feeds == 1u);
}

static void test_stale_task_and_clock_rollback_withhold_feed(void)
{
    fake_backend_t backend = {0u, 0u, true, true};
    openref_watchdog_backend_t hooks = {configure, feed, &backend};
    openref_watchdog_gate_config_t gate_config = config();
    openref_watchdog_driver_t driver;
    assert(openref_watchdog_driver_init(&driver, &gate_config, hooks, 250u, 100u));
    assert(openref_watchdog_driver_report(&driver, 0u, 110u));
    assert(openref_watchdog_driver_report(&driver, 1u, 110u));
    assert(openref_watchdog_driver_tick(&driver, 110u));
    assert(openref_watchdog_driver_report(&driver, 0u, 120u));
    assert(!openref_watchdog_driver_tick(&driver, 170u));
    assert(!openref_watchdog_driver_tick(&driver, 90u));
    assert(backend.feeds == 1u);
}

static void test_backend_failure_latches_and_never_retries(void)
{
    fake_backend_t backend = {0u, 0u, true, false};
    openref_watchdog_backend_t hooks = {configure, feed, &backend};
    openref_watchdog_gate_config_t gate_config = config();
    openref_watchdog_driver_t driver;
    assert(openref_watchdog_driver_init(&driver, &gate_config, hooks, 250u, 0u));
    assert(openref_watchdog_driver_report(&driver, 0u, 1u));
    assert(openref_watchdog_driver_report(&driver, 1u, 1u));
    assert(!openref_watchdog_driver_tick(&driver, 1u));
    assert(driver.fault_latched && driver.backend_failure_count == 1u);
    backend.feed_ok = true;
    assert(!openref_watchdog_driver_report(&driver, 0u, 2u));
    assert(!openref_watchdog_driver_tick(&driver, 2u));
    assert(backend.feeds == 1u);
}

static void test_configuration_failure_is_fail_closed(void)
{
    fake_backend_t backend = {0u, 0u, false, true};
    openref_watchdog_backend_t hooks = {configure, feed, &backend};
    openref_watchdog_gate_config_t gate_config = config();
    openref_watchdog_driver_t driver;
    assert(!openref_watchdog_driver_init(&driver, &gate_config, hooks, 250u, 0u));
    assert(driver.fault_latched && !driver.initialized);
    assert(!openref_watchdog_driver_tick(&driver, 1u));
}

int main(void)
{
    test_feeds_only_after_all_tasks_progress();
    test_stale_task_and_clock_rollback_withhold_feed();
    test_backend_failure_latches_and_never_retries();
    test_configuration_failure_is_fail_closed();
    return 0;
}
