#include "openref_watchdog_fg23_sdk.h"

#ifdef OPENREF_APP_WATCHDOG

#include "em_cmu.h"
#include "em_wdog.h"
#include "rail.h"

static WDOG_PeriodSel_TypeDef select_period(uint32_t minimum_timeout_ms)
{
    static const uint32_t periods_ms[] = {
        9u, 17u, 33u, 65u, 129u, 257u, 513u, 1025u,
        2049u, 4097u, 8193u, 16385u, 32769u, 65537u, 131073u, 262145u,
    };
    for (uint8_t index = 0u; index < 16u; index++) {
        if (periods_ms[index] >= minimum_timeout_ms) {
            return (WDOG_PeriodSel_TypeDef)index;
        }
    }
    return wdogPeriod_256k;
}

static bool hardware_init(void *context, uint32_t minimum_timeout_ms)
{
    (void)context;
    if (minimum_timeout_ms > 262145u) {
        return false;
    }
    CMU_ClockSelectSet(cmuClock_WDOG0CLK, cmuSelect_ULFRCO);
    CMU_ClockEnable(cmuClock_WDOG0, true);
    WDOG_Init_TypeDef init = WDOG_INIT_DEFAULT;
    init.debugRun = false;
    init.em1Run = true;
    init.em2Run = true;
    init.em3Run = false;
    init.lock = true;
    init.perSel = select_period(minimum_timeout_ms);
    WDOGn_Init(WDOG0, &init);
    return WDOGn_IsEnabled(WDOG0);
}

static bool hardware_feed(void *context)
{
    (void)context;
    if (!WDOGn_IsEnabled(WDOG0)) {
        return false;
    }
    WDOGn_Feed(WDOG0);
    return true;
}

static uint32_t clock_us(void *context)
{
    (void)context;
    return RAIL_GetTime();
}

openref_watchdog_fg23_hooks_t openref_watchdog_fg23_sdk_hooks(void)
{
    openref_watchdog_fg23_hooks_t hooks = {
        hardware_init, hardware_feed, clock_us, NULL,
    };
    return hooks;
}

#else

openref_watchdog_fg23_hooks_t openref_watchdog_fg23_sdk_hooks(void)
{
    return (openref_watchdog_fg23_hooks_t){0};
}

#endif
