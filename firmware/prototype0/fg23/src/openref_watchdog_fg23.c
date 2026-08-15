#include "openref_watchdog_fg23.h"

#include <stddef.h>

#if defined(OPENREF_APP_WATCHDOG_FG23)
#include "em_wdog.h"
#endif

static const uint32_t watchdog_period_ms[] = {
    9u, 17u, 33u, 65u, 129u, 257u, 513u, 1025u,
    2049u, 4097u, 8193u, 16385u, 32769u, 65537u, 131073u, 262145u,
};

bool openref_watchdog_fg23_select_period(
    uint32_t requested_timeout_ms,
    uint8_t *period_selector,
    uint32_t *effective_timeout_ms)
{
    size_t index;

    if (requested_timeout_ms == 0u || period_selector == NULL ||
        effective_timeout_ms == NULL) {
        return false;
    }
    for (index = 0u; index <
         (sizeof(watchdog_period_ms) / sizeof(watchdog_period_ms[0])); index++) {
        if (watchdog_period_ms[index] >= requested_timeout_ms) {
            *period_selector = (uint8_t)index;
            *effective_timeout_ms = watchdog_period_ms[index];
            return true;
        }
    }
    return false;
}

bool openref_watchdog_fg23_configure(void *context, uint32_t timeout_ms)
{
    openref_watchdog_fg23_t *target = context;
    uint8_t selector;
    uint32_t effective_timeout_ms;

    if (target == NULL || target->configured ||
        !openref_watchdog_fg23_select_period(
            timeout_ms, &selector, &effective_timeout_ms)) {
        return false;
    }

#if defined(OPENREF_APP_WATCHDOG_FG23)
    {
        WDOG_Init_TypeDef init = WDOG_INIT_DEFAULT;
        init.debugRun = false;
        init.em1Run = true;
        init.em2Run = true;
        init.em3Run = true;
        init.lock = true;
        init.perSel = (WDOG_PeriodSel_TypeDef)selector;
        WDOGn_Init(WDOG0, &init);
        WDOGn_SyncWait(WDOG0);
    }
    target->requested_timeout_ms = timeout_ms;
    target->effective_timeout_ms = effective_timeout_ms;
    target->period_selector = selector;
    target->configured = true;
    return true;
#else
    (void)selector;
    (void)effective_timeout_ms;
    return false;
#endif
}

bool openref_watchdog_fg23_feed(void *context)
{
    openref_watchdog_fg23_t *target = context;

    if (target == NULL || !target->configured) {
        return false;
    }
#if defined(OPENREF_APP_WATCHDOG_FG23)
    WDOGn_Feed(WDOG0);
    return true;
#else
    return false;
#endif
}

uint64_t openref_watchdog_fg23_monotonic_ms(
    openref_watchdog_fg23_clock_t *clock,
    uint32_t raw_time_us)
{
    if (clock == NULL) {
        return 0u;
    }
    if (!clock->initialized) {
        clock->previous_us = raw_time_us;
        clock->initialized = true;
    } else {
        if (raw_time_us < clock->previous_us) {
            clock->epoch_us += (UINT64_C(1) << 32);
        }
        clock->previous_us = raw_time_us;
    }
    return (clock->epoch_us + raw_time_us) / UINT64_C(1000);
}

openref_watchdog_backend_t openref_watchdog_fg23_backend(
    openref_watchdog_fg23_t *context)
{
    openref_watchdog_backend_t backend;
    backend.configure = openref_watchdog_fg23_configure;
    backend.feed = openref_watchdog_fg23_feed;
    backend.context = context;
    return backend;
}
