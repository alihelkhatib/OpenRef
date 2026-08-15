#include <assert.h>
#include <string.h>

#include "openref_crew_session.h"

typedef struct {
    bool install_ok;
    bool erase_ok;
    uint32_t installed_id;
    uint8_t installed_key[OPENREF_CREW_SESSION_KEY_BYTES];
} backend_state_t;

static bool install_key(void *context, uint32_t id, const uint8_t *key)
{
    backend_state_t *state = context;
    state->installed_id = id;
    memcpy(state->installed_key, key, OPENREF_CREW_SESSION_KEY_BYTES);
    return state->install_ok;
}

static bool erase_key(void *context)
{
    return ((backend_state_t *)context)->erase_ok;
}

static void fill_key(uint8_t *key)
{
    memset(key, 0x5au, OPENREF_CREW_SESSION_KEY_BYTES);
}

static void test_activation_leave_and_no_key_retention(void)
{
    backend_state_t backend_state = {.install_ok = true, .erase_ok = true};
    openref_crew_session_t session;
    openref_crew_key_backend_t backend = {install_key, erase_key, &backend_state};
    assert(openref_crew_session_init(&session, 2u, backend));
    openref_crew_admission_t admission = {
        .session_id = 42u,
        .member_mask = 0x07u,
        .member_count = 3u,
        .local_node_id = 2u,
        .authenticated = true,
    };
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES];
    fill_key(key);
    assert(openref_crew_session_activate(&session, &admission, key));
    assert(backend_state.installed_id == 42u);
    assert(backend_state.installed_key[0] == 0x5au);
    for (uint8_t i = 0u; i < sizeof(key); i++) {
        assert(key[i] == 0u);
    }
    assert(openref_crew_session_contains(&session, 1u));
    assert(openref_crew_session_contains(&session, 2u));
    assert(!openref_crew_session_contains(&session, 4u));
    assert(openref_crew_session_leave(&session));
    assert(!session.active);

    fill_key(key);
    assert(!openref_crew_session_activate(&session, &admission, key));
    assert(session.rejected_admissions == 1u);
}

static void test_rejects_unauthenticated_or_inconsistent_admission(void)
{
    backend_state_t backend_state = {.install_ok = true, .erase_ok = true};
    openref_crew_session_t session;
    openref_crew_key_backend_t backend = {install_key, erase_key, &backend_state};
    assert(openref_crew_session_init(&session, 1u, backend));
    openref_crew_admission_t admission = {
        .session_id = 8u, .member_mask = 0x03u, .member_count = 2u,
        .local_node_id = 1u,
    };
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES];
    fill_key(key);
    assert(!openref_crew_session_activate(&session, &admission, key));
    admission.authenticated = true;
    admission.member_count = 3u;
    fill_key(key);
    assert(!openref_crew_session_activate(&session, &admission, key));
    assert(backend_state.installed_id == 0u);
}

static void test_backend_failures_fail_closed(void)
{
    backend_state_t backend_state = {.install_ok = false, .erase_ok = false};
    openref_crew_session_t session;
    openref_crew_key_backend_t backend = {install_key, erase_key, &backend_state};
    assert(openref_crew_session_init(&session, 1u, backend));
    openref_crew_admission_t admission = {
        .session_id = 9u, .member_mask = 0x03u, .member_count = 2u,
        .local_node_id = 1u,
        .authenticated = true,
    };
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES];
    fill_key(key);
    assert(!openref_crew_session_activate(&session, &admission, key));
    assert(!session.active);
    assert(session.backend_failures == 1u);
    assert(!openref_crew_session_leave(&session));
    assert(session.backend_failures == 2u);
}

int main(void)
{
    test_activation_leave_and_no_key_retention();
    test_rejects_unauthenticated_or_inconsistent_admission();
    test_backend_failures_fail_closed();
    return 0;
}
