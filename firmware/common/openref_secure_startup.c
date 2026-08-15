#include "openref_secure_startup.h"

#include <stddef.h>
#include <string.h>

bool openref_secure_startup_init(
    openref_secure_startup_t *startup,
    openref_boot_counter_read_fn read_counter,
    openref_boot_counter_write_fn write_counter,
    void *counter_context,
    openref_radio_session_backend_t radio_backend)
{
    if (startup == NULL) {
        return false;
    }
    memset(startup, 0, sizeof(*startup));
    uint32_t advanced_boot_counter = 0u;
    if (!openref_boot_counter_advance(read_counter, write_counter,
            counter_context, &advanced_boot_counter)) {
        return false;
    }
    return openref_secure_startup_init_advanced(
        startup, advanced_boot_counter, radio_backend);
}

bool openref_secure_startup_init_advanced(
    openref_secure_startup_t *startup,
    uint32_t advanced_boot_counter,
    openref_radio_session_backend_t radio_backend)
{
    if (startup == NULL || advanced_boot_counter == 0u) {
        return false;
    }
    memset(startup, 0, sizeof(*startup));
    startup->active_boot_counter = advanced_boot_counter;
    if (!openref_radio_session_init(&startup->radio_session, radio_backend,
            advanced_boot_counter)) {
        return false;
    }
    startup->initialized = true;
    return true;
}

openref_crew_key_backend_t openref_secure_startup_crew_key_backend(
    openref_secure_startup_t *startup)
{
    if (startup == NULL || !startup->initialized) {
        return (openref_crew_key_backend_t){0};
    }
    return openref_radio_session_crew_key_backend(&startup->radio_session);
}
