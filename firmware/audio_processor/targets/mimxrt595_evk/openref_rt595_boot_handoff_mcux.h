#ifndef OPENREF_RT595_BOOT_HANDOFF_MCUX_H
#define OPENREF_RT595_BOOT_HANDOFF_MCUX_H
#include <stdbool.h>
#include "openref_rt595_boot_handoff.h"
bool openref_rt595_boot_handoff_mcux_prepare(const openref_rt595_boot_handoff_layout_t *,openref_rt595_boot_handoff_plan_t *);
void openref_rt595_boot_handoff_mcux_execute(const openref_rt595_boot_handoff_plan_t *) __attribute__((noreturn));
#endif
