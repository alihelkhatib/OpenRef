#include "openref_radio_session.h"

#include <stddef.h>
#include <string.h>

static bool install(void *context, uint32_t session_id,
    const uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES])
{
    openref_radio_session_t *radio_session = context;
    if (radio_session == NULL || key == NULL || session_id == 0u ||
        radio_session->active ||
        !radio_session->backend.provision(radio_session->backend.context,
            session_id, radio_session->boot_counter, 1u, key)) {
        if (radio_session != NULL) {
            radio_session->failures++;
        }
        return false;
    }
    radio_session->active_session_id = session_id;
    radio_session->active = true;
    radio_session->provisions++;
    return true;
}

static bool erase(void *context)
{
    openref_radio_session_t *radio_session = context;
    if (radio_session == NULL) {
        return false;
    }
    bool disabled = radio_session->backend.disable(
        radio_session->backend.context);
    radio_session->active = false;
    radio_session->active_session_id = 0u;
    if (!disabled) {
        radio_session->failures++;
        return false;
    }
    radio_session->disables++;
    return true;
}

bool openref_radio_session_init(
    openref_radio_session_t *radio_session,
    openref_radio_session_backend_t backend,
    uint32_t advanced_boot_counter)
{
    if (radio_session == NULL || backend.provision == NULL ||
        backend.disable == NULL || advanced_boot_counter == 0u) {
        return false;
    }
    memset(radio_session, 0, sizeof(*radio_session));
    radio_session->backend = backend;
    radio_session->boot_counter = advanced_boot_counter;
    return backend.disable(backend.context);
}

openref_crew_key_backend_t openref_radio_session_crew_key_backend(
    openref_radio_session_t *radio_session)
{
    openref_crew_key_backend_t backend = {0};
    if (radio_session != NULL) {
        backend.install = install;
        backend.erase = erase;
        backend.context = radio_session;
    }
    return backend;
}
