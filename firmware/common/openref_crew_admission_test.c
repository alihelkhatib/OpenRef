#include "openref_crew_admission.h"

#include <assert.h>
#include <string.h>

typedef struct {
    bool verify_ok;
    bool unwrap_ok;
    bool persist_ok;
    bool install_ok;
    bool erase_ok;
    uint32_t persisted_counter;
    uint32_t installed_session_id;
    uint32_t verify_calls;
    uint32_t unwrap_calls;
} backend_state_t;

static bool verify_invitation(void *context, const uint8_t *signed_data,
    const uint8_t *fingerprint, const uint8_t *signature)
{
    backend_state_t *state = context;
    state->verify_calls++;
    return state->verify_ok && signed_data[0] == 0x4fu &&
        fingerprint[0] != 0u && signature[0] != 0u;
}

static bool unwrap_key(void *context, const uint8_t *wrapped_key,
    const uint8_t *challenge, uint32_t session_id, uint8_t *key)
{
    backend_state_t *state = context;
    state->unwrap_calls++;
    if (!state->unwrap_ok || wrapped_key[0] == 0u || challenge[0] == 0u ||
        session_id == 0u) {
        return false;
    }
    memset(key, 0x5au, OPENREF_CREW_SESSION_KEY_BYTES);
    return true;
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

static bool install_key(void *context, uint32_t session_id, const uint8_t *key)
{
    backend_state_t *state = context;
    if (!state->install_ok || key[0] != 0x5au) {
        return false;
    }
    state->installed_session_id = session_id;
    return true;
}

static bool erase_key(void *context)
{
    return ((backend_state_t *)context)->erase_ok;
}

static void write_u32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16);
    data[3] = (uint8_t)(value >> 24);
}

static void make_invitation(uint8_t *wire, const uint8_t *challenge,
    uint8_t local_node_id, uint32_t session_id, uint32_t counter)
{
    memset(wire, 0, OPENREF_ADMISSION_WIRE_BYTES);
    wire[0] = 0x4fu;
    wire[1] = 0x52u;
    wire[2] = 0x4au;
    wire[3] = 0x4eu;
    wire[4] = 1u;
    wire[5] = local_node_id;
    wire[6] = 0x07u;
    wire[7] = 3u;
    write_u32(&wire[8], session_id);
    write_u32(&wire[12], counter);
    memcpy(&wire[16], challenge, OPENREF_ADMISSION_CHALLENGE_BYTES);
    memset(&wire[48], 0x11, 8u);
    memset(&wire[56], 0x22, 16u);
    memset(&wire[72], 0x33, OPENREF_ADMISSION_WRAPPED_KEY_BYTES);
    memset(&wire[OPENREF_ADMISSION_SIGNED_BYTES], 0x44,
        OPENREF_ADMISSION_SIGNATURE_BYTES);
}

static void initialize(openref_crew_session_t *session,
    openref_crew_admission_protocol_t *protocol, backend_state_t *state)
{
    openref_crew_key_backend_t key_backend = {
        .install = install_key, .erase = erase_key, .context = state};
    assert(openref_crew_session_init(session, 2u, key_backend));
    openref_admission_backend_t admission_backend = {
        .verify = verify_invitation,
        .unwrap = unwrap_key,
        .persist_counter = persist_counter,
        .context = state,
    };
    openref_admission_config_t config = {
        .invitation_window_ms = 5000u,
        .lockout_ms = 10000u,
        .maximum_failures = 2u,
    };
    assert(openref_crew_admission_init(protocol, &config, admission_backend,
        session, 7u, 100u));
}

static void test_valid_invitation_activates_session(void)
{
    backend_state_t state = {.verify_ok = true, .unwrap_ok = true,
        .persist_ok = true, .install_ok = true, .erase_ok = true};
    openref_crew_session_t session;
    openref_crew_admission_protocol_t protocol;
    initialize(&session, &protocol, &state);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES] = {1u};
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];
    make_invitation(wire, challenge, 2u, 42u, 8u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 101u));
    assert(openref_crew_admission_accept(&protocol, wire, 102u));
    assert(session.active && session.active_session_id == 42u);
    assert(session.local_node_id == 2u && state.installed_session_id == 42u);
    assert(state.persisted_counter == 8u);
    assert(protocol.accepted_invitations == 1u && !protocol.invitation_open);
}

static void test_requires_physical_confirmation_and_live_challenge(void)
{
    backend_state_t state = {.verify_ok = true, .unwrap_ok = true,
        .persist_ok = true, .install_ok = true, .erase_ok = true};
    openref_crew_session_t session;
    openref_crew_admission_protocol_t protocol;
    initialize(&session, &protocol, &state);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES] = {2u};
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];
    make_invitation(wire, challenge, 2u, 43u, 8u);
    assert(!openref_crew_admission_begin(&protocol, false, challenge, 101u));
    assert(!openref_crew_admission_accept(&protocol, wire, 102u));
    assert(state.verify_calls == 0u && state.unwrap_calls == 0u);
    assert(!session.active);
}

static void test_identity_counter_and_window_fail_closed(void)
{
    backend_state_t state = {.verify_ok = true, .unwrap_ok = true,
        .persist_ok = true, .install_ok = true, .erase_ok = true};
    openref_crew_session_t session;
    openref_crew_admission_protocol_t protocol;
    initialize(&session, &protocol, &state);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES] = {3u};
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];

    make_invitation(wire, challenge, 1u, 44u, 8u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 101u));
    assert(!openref_crew_admission_accept(&protocol, wire, 102u));
    assert(!session.active);
    assert(state.verify_calls == 0u && state.unwrap_calls == 0u);
    assert(state.persisted_counter == 0u);

    make_invitation(wire, challenge, 2u, 44u, 7u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 103u));
    assert(!openref_crew_admission_accept(&protocol, wire, 104u));
    assert(!openref_crew_admission_begin(&protocol, true, challenge, 105u));
    assert(!session.active);

    assert(openref_crew_admission_begin(&protocol, true, challenge, 10104u));
    make_invitation(wire, challenge, 2u, 44u, 8u);
    assert(!openref_crew_admission_accept(&protocol, wire, 15105u));
    assert(!session.active);
}

static void test_backend_failure_never_activates(void)
{
    backend_state_t state = {.verify_ok = true, .unwrap_ok = true,
        .persist_ok = false, .install_ok = true, .erase_ok = true};
    openref_crew_session_t session;
    openref_crew_admission_protocol_t protocol;
    initialize(&session, &protocol, &state);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES] = {4u};
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];
    make_invitation(wire, challenge, 2u, 45u, 8u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 101u));
    assert(!openref_crew_admission_accept(&protocol, wire, 102u));
    assert(!session.active && state.installed_session_id == 0u);
}

int main(void)
{
    test_valid_invitation_activates_session();
    test_requires_physical_confirmation_and_live_challenge();
    test_identity_counter_and_window_fail_closed();
    test_backend_failure_never_activates();
    return 0;
}
