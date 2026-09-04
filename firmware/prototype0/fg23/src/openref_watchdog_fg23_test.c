#include <assert.h>
#include <stdint.h>

#include "openref_watchdog_fg23.h"

typedef struct {
    uint32_t now_us;
    uint32_t init_calls;
    uint32_t feed_calls;
    uint32_t requested_timeout_ms;
    bool init_ok;
    bool feed_ok;
} fake_hal_t;

static bool hardware_init(void *context, uint32_t timeout_ms)
{
    fake_hal_t *hal = context;
    hal->init_calls++;
    hal->requested_timeout_ms = timeout_ms;
    return hal->init_ok;
}

static bool hardware_feed(void *context)
{
    fake_hal_t *hal = context;
    hal->feed_calls++;
    return hal->feed_ok;
}

static uint32_t clock_us(void *context)
{
    return ((fake_hal_t *)context)->now_us;
}

static openref_watchdog_fg23_t initialized(fake_hal_t *hal)
{
    openref_watchdog_fg23_config_t config = {
        .gate = {
            .required_mask = 0x03u,
            .startup_grace_ms = 100u,
            .task_timeout_ms = {50u, 60u},
        },
        .hardware_timeout_ms = 1000u,
    };
    openref_watchdog_fg23_hooks_t hooks = {
        hardware_init, hardware_feed, clock_us, hal,
    };
    openref_watchdog_fg23_t watchdog;
    assert(openref_watchdog_fg23_init(&watchdog, &config, hooks));
    assert(hal->init_calls == 1u && hal->requested_timeout_ms == 1000u);
    return watchdog;
}

static void test_feeds_only_after_every_task_progresses(void)
{
    fake_hal_t hal = {.init_ok = true, .feed_ok = true};
    openref_watchdog_fg23_t watchdog = initialized(&hal);
    hal.now_us = 10000u;
    assert(openref_watchdog_fg23_report(&watchdog, 0u));
    assert(!openref_watchdog_fg23_process(&watchdog));
    assert(hal.feed_calls == 0u);
    hal.now_us = 11000u;
    assert(openref_watchdog_fg23_report(&watchdog, 1u));
    assert(openref_watchdog_fg23_process(&watchdog));
    assert(hal.feed_calls == 1u && watchdog.gate.feed_count == 1u);
}

static void test_stale_task_withholds_hardware_feed(void)
{
    fake_hal_t hal = {.init_ok = true, .feed_ok = true};
    openref_watchdog_fg23_t watchdog = initialized(&hal);
    assert(openref_watchdog_fg23_report(&watchdog, 0u));
    assert(openref_watchdog_fg23_report(&watchdog, 1u));
    assert(openref_watchdog_fg23_process(&watchdog));
    hal.now_us = 51000u;
    assert(!openref_watchdog_fg23_process(&watchdog));
    assert(hal.feed_calls == 1u);
    assert(watchdog.gate.last_fault_mask == 0x01u);
}

static void test_feed_failure_is_observable(void)
{
    fake_hal_t hal = {.init_ok = true, .feed_ok = false};
    openref_watchdog_fg23_t watchdog = initialized(&hal);
    assert(openref_watchdog_fg23_report(&watchdog, 0u));
    assert(openref_watchdog_fg23_report(&watchdog, 1u));
    assert(!openref_watchdog_fg23_process(&watchdog));
    assert(watchdog.hardware_feed_failures == 1u);
}

static void test_extends_rail_microsecond_wrap(void)
{
    fake_hal_t hal = {
        .now_us = UINT32_MAX - 500u,
        .init_ok = true,
        .feed_ok = true,
    };
    openref_watchdog_fg23_t watchdog = initialized(&hal);
    hal.now_us = 499u;
    assert(openref_watchdog_fg23_report(&watchdog, 0u));
    assert(openref_watchdog_fg23_report(&watchdog, 1u));
    assert(openref_watchdog_fg23_process(&watchdog));
    assert(!watchdog.clock_fault_latched && watchdog.clock_faults == 0u);
}

static void test_clock_rollback_latches_and_withholds_feed(void)
{
    fake_hal_t hal = {.now_us = 10000u, .init_ok = true, .feed_ok = true};
    openref_watchdog_fg23_t watchdog = initialized(&hal);
    hal.now_us = 9000u;
    assert(!openref_watchdog_fg23_report(&watchdog, 0u));
    assert(watchdog.clock_fault_latched && watchdog.clock_faults == 1u);
    assert(!openref_watchdog_fg23_process(&watchdog));
    assert(hal.feed_calls == 0u);
}

static void test_invalid_timeout_does_not_start_hardware(void)
{
    fake_hal_t hal = {.init_ok = true, .feed_ok = true};
    openref_watchdog_fg23_config_t config = {
        .gate = {
            .required_mask = 1u,
            .startup_grace_ms = 100u,
            .task_timeout_ms = {50u},
        },
        .hardware_timeout_ms = 100u,
    };
    openref_watchdog_fg23_hooks_t hooks = {
        hardware_init, hardware_feed, clock_us, &hal,
    };
    openref_watchdog_fg23_t watchdog;
    assert(!openref_watchdog_fg23_init(&watchdog, &config, hooks));
    assert(hal.init_calls == 0u && !watchdog.initialized);
}

int main(void)
{
    test_feeds_only_after_every_task_progresses();
    test_stale_task_withholds_hardware_feed();
    test_feed_failure_is_observable();
    test_extends_rail_microsecond_wrap();
    test_clock_rollback_latches_and_withholds_feed();
    test_invalid_timeout_does_not_start_hardware();
    return 0;
}
