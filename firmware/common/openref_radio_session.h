#ifndef OPENREF_RADIO_SESSION_H
#define OPENREF_RADIO_SESSION_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_crew_session.h"

typedef bool (*openref_radio_session_provision_fn)(
    void *context,
    uint32_t crew_session_id,
    uint32_t boot_counter,
    uint32_t initial_packet_counter,
    const uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES]);
typedef bool (*openref_radio_session_disable_fn)(void *context);

typedef struct {
    openref_radio_session_provision_fn provision;
    openref_radio_session_disable_fn disable;
    void *context;
} openref_radio_session_backend_t;

typedef struct {
    openref_radio_session_backend_t backend;
    uint32_t boot_counter;
    uint32_t active_session_id;
    uint32_t provisions;
    uint32_t disables;
    uint32_t failures;
    bool active;
} openref_radio_session_t;

bool openref_radio_session_init(
    openref_radio_session_t *radio_session,
    openref_radio_session_backend_t backend,
    uint32_t advanced_boot_counter);

openref_crew_key_backend_t openref_radio_session_crew_key_backend(
    openref_radio_session_t *radio_session);

#endif
