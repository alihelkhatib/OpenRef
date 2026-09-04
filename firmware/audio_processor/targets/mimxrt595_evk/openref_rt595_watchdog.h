#ifndef OPENREF_RT595_WATCHDOG_H
#define OPENREF_RT595_WATCHDOG_H

#include <stdbool.h>
#include <stdint.h>

bool openref_rt595_watchdog_init(uint32_t timeout_ms);
void openref_rt595_watchdog_feed(void);

#endif
