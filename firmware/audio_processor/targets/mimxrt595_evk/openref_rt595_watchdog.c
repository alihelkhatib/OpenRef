#include "openref_rt595_watchdog.h"

#include "fsl_clock.h"
#include "fsl_power.h"
#include "fsl_wwdt.h"

bool openref_rt595_watchdog_init(uint32_t timeout_ms)
{
    SYSCTL0->PDRUNCFG0_CLR = SYSCTL0_PDRUNCFG0_LPOSC_PD_MASK;
    CLOCK_AttachClk(kLPOSC_to_WDT0_CLK);
    POWER_DisablePD(kPDRUNCFG_PD_LPOSC);

    uint32_t input_hz = CLOCK_GetWdtClkFreq(0u);
    uint64_t count = ((uint64_t)input_hz * timeout_ms) / 4000u;
    if (timeout_ms == 0u || input_hz == 0u || count < 0xffu || count > 0xffffffu) {
        return false;
    }

    wwdt_config_t config;
    WWDT_GetDefaultConfig(&config);
    config.enableWatchdogReset = true;
    config.enableWatchdogProtect = true;
    config.enableLockOscillator = true;
    config.windowValue = 0xffffffu;
    config.timeoutValue = (uint32_t)count;
    config.warningValue = 0u;
    config.clockFreq_Hz = input_hz;
    WWDT_Init(WWDT0, &config);
    return true;
}

void openref_rt595_watchdog_feed(void)
{
    WWDT_Refresh(WWDT0);
}
