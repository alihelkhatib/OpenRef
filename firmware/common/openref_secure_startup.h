#ifndef OPENREF_SECURE_STARTUP_H
#define OPENREF_SECURE_STARTUP_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_boot_counter.h"
#include "openref_radio_session.h"

typedef struct {
    openref_radio_session_t radio_session;
    uint32_t active_boot_counter;
    bool initialized;
} openref_secure_startup_t;

bool openref_secure_startup_init(
    openref_secure_startup_t *startup,
    openref_boot_counter_read_fn read_counter,
    openref_boot_counter_write_fn write_counter,
    void *counter_context,
    openref_radio_session_backend_t radio_backend);

bool openref_secure_startup_init_advanced(
    openref_secure_startup_t *startup,
    uint32_t advanced_boot_counter,
    openref_radio_session_backend_t radio_backend);

openref_crew_key_backend_t openref_secure_startup_crew_key_backend(
    openref_secure_startup_t *startup);

#endif
