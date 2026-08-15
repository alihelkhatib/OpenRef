#include <assert.h>
#include <string.h>

#include "openref_service_session.h"

typedef struct {
    bool verify_ok;
    bool persist_ok;
    uint32_t persisted_counter;
} backend_state_t;

static bool verify(void *context, const uint8_t *challenge, uint32_t counter,
    openref_service_role_t role, uint32_t permissions, const uint8_t *response)
{
    backend_state_t *state = context;
    return state->verify_ok && challenge[0] == 0x11u && counter != 0u &&
        role != 0 && permissions != 0u && response[0] == 0x22u;
}

static bool persist_counter(void *context, uint32_t counter)
{
    backend_state_t *state = context;
    if (!state->persist_ok) {
        return false;
    }
    state->persisted_counter = counter;
    return true;
}

static openref_service_session_t make_session(backend_state_t *state)
{
    openref_service_config_t config = {100u, 1000u, 500u, 3u};
    openref_service_backend_t backend = {verify, persist_counter, state};
    openref_service_session_t session;
    assert(openref_service_session_init(&session, &config, backend, 10u, 0u));
    return session;
}

static void credentials(uint8_t *challenge, uint8_t *response)
{
    memset(challenge, 0x11, OPENREF_SERVICE_CHALLENGE_BYTES);
    memset(response, 0x22, OPENREF_SERVICE_RESPONSE_BYTES);
}

static void test_authorized_least_privilege_and_expiry(void)
{
    backend_state_t state = {.verify_ok = true, .persist_ok = true};
    openref_service_session_t session = make_session(&state);
    uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES];
    uint8_t response[OPENREF_SERVICE_RESPONSE_BYTES];
    credentials(challenge, response);
    assert(openref_service_issue_challenge(&session, challenge, 1u));
    uint32_t permissions = OPENREF_SERVICE_PERMISSION_DIAGNOSTICS |
        OPENREF_SERVICE_PERMISSION_CONFIG_READ;
    assert(openref_service_authorize(&session, 11u,
        OPENREF_SERVICE_ROLE_FIELD, permissions, false, response, 2u));
    assert(state.persisted_counter == 11u);
    assert(openref_service_permitted(&session,
        OPENREF_SERVICE_PERMISSION_DIAGNOSTICS, 3u));
    assert(!openref_service_permitted(&session,
        OPENREF_SERVICE_PERMISSION_CONFIG_WRITE, 3u));
    assert(!openref_service_permitted(&session,
        OPENREF_SERVICE_PERMISSION_DIAGNOSTICS, 1003u));
    assert(!session.session_active);
}

static void test_role_presence_replay_and_expired_challenge(void)
{
    backend_state_t state = {.verify_ok = true, .persist_ok = true};
    openref_service_session_t session = make_session(&state);
    uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES];
    uint8_t response[OPENREF_SERVICE_RESPONSE_BYTES];
    credentials(challenge, response);
    assert(openref_service_issue_challenge(&session, challenge, 1u));
    assert(!openref_service_authorize(&session, 11u,
        OPENREF_SERVICE_ROLE_FIELD, OPENREF_SERVICE_PERMISSION_CONFIG_WRITE,
        true, response, 2u));
    assert(openref_service_issue_challenge(&session, challenge, 3u));
    assert(!openref_service_authorize(&session, 11u,
        OPENREF_SERVICE_ROLE_TECHNICIAN,
        OPENREF_SERVICE_PERMISSION_CONFIG_WRITE, false, response, 4u));
    assert(openref_service_issue_challenge(&session, challenge, 5u));
    assert(!openref_service_authorize(&session, 11u,
        OPENREF_SERVICE_ROLE_TECHNICIAN,
        OPENREF_SERVICE_PERMISSION_CONFIG_WRITE, true, response, 106u));
}

static void test_lockout_persistence_failure_and_clock_rollback(void)
{
    backend_state_t state = {.verify_ok = false, .persist_ok = true};
    openref_service_session_t session = make_session(&state);
    uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES];
    uint8_t response[OPENREF_SERVICE_RESPONSE_BYTES];
    credentials(challenge, response);
    for (uint64_t attempt = 1u; attempt <= 3u; attempt++) {
        assert(openref_service_issue_challenge(&session, challenge,
                                               attempt * 2u));
        assert(!openref_service_authorize(&session, (uint32_t)(10u + attempt),
            OPENREF_SERVICE_ROLE_FIELD, OPENREF_SERVICE_PERMISSION_DIAGNOSTICS,
            false, response, attempt * 2u + 1u));
    }
    assert(!openref_service_issue_challenge(&session, challenge, 10u));
    assert(openref_service_issue_challenge(&session, challenge, 507u));
    state.verify_ok = true;
    state.persist_ok = false;
    assert(!openref_service_authorize(&session, 20u,
        OPENREF_SERVICE_ROLE_FIELD, OPENREF_SERVICE_PERMISSION_DIAGNOSTICS,
        false, response, 508u));
    assert(!session.session_active);
    assert(!openref_service_issue_challenge(&session, challenge, 507u));
}

int main(void)
{
    test_authorized_least_privilege_and_expiry();
    test_role_presence_replay_and_expired_challenge();
    test_lockout_persistence_failure_and_clock_rollback();
    return 0;
}
