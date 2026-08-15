#include "openref_secure_startup_fg23.h"

#include <stddef.h>
#include <string.h>

#include "openref_boot_counter_fg23.h"
#include "openref_radio_session_fg23.h"

bool openref_secure_startup_fg23_init(openref_secure_startup_t *startup)
{
    if (startup == NULL) {
        return false;
    }
    memset(startup, 0, sizeof(*startup));
    uint32_t advanced_boot_counter = 0u;
    return openref_boot_counter_fg23_advance(&advanced_boot_counter) &&
        openref_secure_startup_init_advanced(startup,
            advanced_boot_counter, openref_radio_session_fg23_backend());
}
