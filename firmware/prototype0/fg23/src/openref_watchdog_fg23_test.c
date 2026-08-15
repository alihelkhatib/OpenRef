#include <assert.h>
#include <string.h>

#include "openref_watchdog_fg23.h"

static void test_period_selection_is_bounded_and_never_shorter(void)
{
    uint8_t selector = 0xffu;
    uint32_t effective = 0u;
    assert(!openref_watchdog_fg23_select_period(0u, &selector, &effective));
    assert(openref_watchdog_fg23_select_period(9u, &selector, &effective));
    assert(selector == 0u && effective == 9u);
    assert(openref_watchdog_fg23_select_period(250u, &selector, &effective));
    assert(selector == 5u && effective == 257u);
    assert(openref_watchdog_fg23_select_period(262145u, &selector, &effective));
    assert(selector == 15u && effective == 262145u);
    assert(!openref_watchdog_fg23_select_period(262146u, &selector, &effective));
}

static void test_disabled_backend_fails_closed(void)
{
    openref_watchdog_fg23_t target;
    openref_watchdog_backend_t backend;
    memset(&target, 0, sizeof(target));
    backend = openref_watchdog_fg23_backend(&target);
    assert(backend.context == &target);
    assert(!backend.configure(backend.context, 250u));
    assert(!target.configured);
    assert(!backend.feed(backend.context));
}

static void test_rail_clock_extension_survives_wrap(void)
{
    openref_watchdog_fg23_clock_t clock;
    uint64_t before;
    uint64_t after;
    memset(&clock, 0, sizeof(clock));
    before = openref_watchdog_fg23_monotonic_ms(&clock, UINT32_MAX - 499u);
    after = openref_watchdog_fg23_monotonic_ms(&clock, 500u);
    assert(after > before);
    assert(after - before == 1u);
    assert(openref_watchdog_fg23_monotonic_ms(NULL, 1u) == 0u);
}

int main(void)
{
    test_period_selection_is_bounded_and_never_shorter();
    test_disabled_backend_fails_closed();
    test_rail_clock_extension_survives_wrap();
    return 0;
}
