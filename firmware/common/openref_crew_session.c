#include "openref_crew_session.h"

#include <stddef.h>
#include <string.h>

static void wipe_key(uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES])
{
    if (key == NULL) {
        return;
    }
    volatile uint8_t *cursor = key;
    for (uint8_t index = 0u; index < OPENREF_CREW_SESSION_KEY_BYTES; index++) {
        cursor[index] = 0u;
    }
}

static uint8_t population(uint8_t mask)
{
    uint8_t count = 0u;
    for (uint8_t bit = 0u; bit < OPENREF_CREW_MAX_MEMBERS; bit++) {
        count += (uint8_t)((mask >> bit) & 1u);
    }
    return count;
}

bool openref_crew_session_init(
    openref_crew_session_t *session,
    uint8_t local_node_id,
    openref_crew_key_backend_t backend)
{
    if (session == NULL || local_node_id > OPENREF_CREW_MAX_MEMBERS ||
        backend.install == NULL || backend.erase == NULL) {
        return false;
    }
    memset(session, 0, sizeof(*session));
    session->backend = backend;
    session->local_node_id = local_node_id;
    return true;
}

bool openref_crew_session_activate(
    openref_crew_session_t *session,
    const openref_crew_admission_t *admission,
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES])
{
    if (session == NULL || admission == NULL || key == NULL) {
        wipe_key(key);
        return false;
    }
    const uint8_t valid_member_bits = (1u << OPENREF_CREW_MAX_MEMBERS) - 1u;
    const uint8_t local_bit = admission->local_node_id >= 1u &&
        admission->local_node_id <= OPENREF_CREW_MAX_MEMBERS
        ? (uint8_t)(1u << (admission->local_node_id - 1u)) : 0u;
    bool valid = admission->authenticated && admission->session_id != 0u &&
        admission->session_id != session->last_session_id &&
        (admission->member_mask & (uint8_t)~valid_member_bits) == 0u &&
        local_bit != 0u && (admission->member_mask & local_bit) != 0u &&
        admission->member_count >= 2u &&
        admission->member_count <= OPENREF_CREW_MAX_MEMBERS &&
        admission->member_count == population(admission->member_mask);
    if (!valid || session->active) {
        session->rejected_admissions++;
        wipe_key(key);
        return false;
    }
    bool installed = session->backend.install(
        session->backend.context, admission->session_id, key);
    wipe_key(key);
    if (!installed) {
        session->backend_failures++;
        return false;
    }
    session->active_session_id = admission->session_id;
    session->local_node_id = admission->local_node_id;
    session->last_session_id = admission->session_id;
    session->member_mask = admission->member_mask;
    session->active = true;
    session->activations++;
    return true;
}

bool openref_crew_session_leave(openref_crew_session_t *session)
{
    if (session == NULL) {
        return false;
    }
    if (!session->backend.erase(session->backend.context)) {
        session->backend_failures++;
        session->active = false;
        session->active_session_id = 0u;
        session->member_mask = 0u;
        return false;
    }
    session->active = false;
    session->active_session_id = 0u;
    session->member_mask = 0u;
    return true;
}

bool openref_crew_session_contains(
    const openref_crew_session_t *session,
    uint8_t node_id)
{
    return session != NULL && session->active && node_id >= 1u &&
        node_id <= OPENREF_CREW_MAX_MEMBERS &&
        (session->member_mask & (uint8_t)(1u << (node_id - 1u))) != 0u;
}
