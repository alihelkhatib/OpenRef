#include "openref_reset_cause_fg23.h"

#include <stddef.h>

#if defined(OPENREF_APP_RESET_CAUSE_FG23)
#include "em_rmu.h"

_Static_assert(_EMU_RSTCAUSE_POR_MASK == OPENREF_FG23_RESET_RAW_POR, "POR mask changed");
_Static_assert(_EMU_RSTCAUSE_PIN_MASK == OPENREF_FG23_RESET_RAW_PIN, "PIN mask changed");
_Static_assert(_EMU_RSTCAUSE_EM4_MASK == OPENREF_FG23_RESET_RAW_EM4, "EM4 mask changed");
_Static_assert(_EMU_RSTCAUSE_WDOG0_MASK == OPENREF_FG23_RESET_RAW_WDOG0, "WDOG0 mask changed");
_Static_assert(_EMU_RSTCAUSE_WDOG1_MASK == OPENREF_FG23_RESET_RAW_WDOG1, "WDOG1 mask changed");
_Static_assert(_EMU_RSTCAUSE_LOCKUP_MASK == OPENREF_FG23_RESET_RAW_LOCKUP, "LOCKUP mask changed");
_Static_assert(_EMU_RSTCAUSE_SYSREQ_MASK == OPENREF_FG23_RESET_RAW_SYSREQ, "SYSREQ mask changed");
_Static_assert(_EMU_RSTCAUSE_SETAMPER_MASK == OPENREF_FG23_RESET_RAW_SECURITY, "SETAMPER mask changed");
_Static_assert(_EMU_RSTCAUSE_VREGIN_MASK == OPENREF_FG23_RESET_RAW_VREGIN, "VREGIN mask changed");
#endif

uint32_t openref_reset_cause_fg23_classify(uint32_t raw)
{
    uint32_t classified = 0u;
    uint32_t known = OPENREF_FG23_RESET_RAW_POR | OPENREF_FG23_RESET_RAW_PIN |
        OPENREF_FG23_RESET_RAW_EM4 | OPENREF_FG23_RESET_RAW_WDOG0 |
        OPENREF_FG23_RESET_RAW_WDOG1 | OPENREF_FG23_RESET_RAW_LOCKUP |
        OPENREF_FG23_RESET_RAW_SYSREQ | OPENREF_FG23_RESET_RAW_BROWNOUT |
        OPENREF_FG23_RESET_RAW_SECURITY | OPENREF_FG23_RESET_RAW_VREGIN;

    if ((raw & OPENREF_FG23_RESET_RAW_POR) != 0u) classified |= OPENREF_RESET_CAUSE_POWER_ON;
    if ((raw & OPENREF_FG23_RESET_RAW_PIN) != 0u) classified |= OPENREF_RESET_CAUSE_EXTERNAL_PIN;
    if ((raw & OPENREF_FG23_RESET_RAW_EM4) != 0u) classified |= OPENREF_RESET_CAUSE_LOW_POWER_WAKE;
    if ((raw & (OPENREF_FG23_RESET_RAW_WDOG0 | OPENREF_FG23_RESET_RAW_WDOG1)) != 0u)
        classified |= OPENREF_RESET_CAUSE_WATCHDOG;
    if ((raw & OPENREF_FG23_RESET_RAW_LOCKUP) != 0u) classified |= OPENREF_RESET_CAUSE_CORE_LOCKUP;
    if ((raw & OPENREF_FG23_RESET_RAW_SYSREQ) != 0u) classified |= OPENREF_RESET_CAUSE_SOFTWARE;
    if ((raw & (OPENREF_FG23_RESET_RAW_BROWNOUT | OPENREF_FG23_RESET_RAW_VREGIN)) != 0u)
        classified |= OPENREF_RESET_CAUSE_BROWNOUT;
    if ((raw & OPENREF_FG23_RESET_RAW_SECURITY) != 0u) classified |= OPENREF_RESET_CAUSE_SECURITY;
    if (raw == 0u || (raw & ~known) != 0u) classified |= OPENREF_RESET_CAUSE_UNKNOWN;
    return classified;
}

bool openref_reset_cause_fg23_capture(openref_reset_cause_fg23_t *cause)
{
    if (cause == NULL || cause->captured) {
        return false;
    }
#if defined(OPENREF_APP_RESET_CAUSE_FG23)
    cause->raw = RMU_ResetCauseGet();
    cause->classified = openref_reset_cause_fg23_classify(cause->raw);
    cause->captured = true;
    RMU_ResetCauseClear();
    return true;
#else
    return false;
#endif
}
