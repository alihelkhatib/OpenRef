#include <assert.h>
#include <string.h>

#include "openref_crew_admission.h"

typedef struct {
    bool verify_ok;
    bool unwrap_ok;
    bool persist_ok;
    bool install_ok;
    uint32_t persisted_counter;
    uint8_t installed_key;
} backend_state_t;

static bool verify(void *context, const uint8_t *signed_data,
    const uint8_t *fingerprint, const uint8_t *signature)
{
    backend_state_t *state = context;
    return state->verify_ok && signed_data[0] == 0x4fu &&
        fingerprint[0] == 0x33u && signature[0] == 0x55u;
}

static bool unwrap(void *context, const uint8_t *wrapped,
    const uint8_t *challenge, uint32_t session_id, uint8_t *key)
{
    backend_state_t *state = context;
    if (!state->unwrap_ok || wrapped[0] != 0x44u ||
        challenge[0] != 0x22u || session_id == 0u) {
        return false;
    }
    memset(key, 0x66, OPENREF_CREW_SESSION_KEY_BYTES);
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
    state->installed_key = key[0];
    return state->install_ok && session_id != 0u;
}

static bool erase_key(void *context)
{
    (void)context;
    return true;
}

static void write_u32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16);
    data[3] = (uint8_t)(value >> 24);
}

static void make_invitation(uint8_t *wire, const uint8_t *challenge,
                            uint32_t counter)
{
    memset(wire, 0, OPENREF_ADMISSION_WIRE_BYTES);
    wire[0] = 0x4fu;
    wire[1] = 0x52u;
    wire[2] = 0x4au;
    wire[3] = 0x4eu;
    wire[4] = 1u;
    wire[5] = 2u;
    wire[6] = 0x07u;
    wire[7] = 3u;
    write_u32(&wire[8], 0x12345678u);
    write_u32(&wire[12], counter);
    memcpy(&wire[16], challenge, OPENREF_ADMISSION_CHALLENGE_BYTES);
    memset(&wire[48], 0x33, 8u);
    memset(&wire[56], 0x77, 16u);
    memset(&wire[72], 0x44, OPENREF_ADMISSION_WRAPPED_KEY_BYTES);
    wire[104] = 0x55u;
}

static openref_crew_admission_protocol_t make_protocol(
    backend_state_t *state, openref_crew_session_t *crew, uint32_t counter)
{
    openref_crew_key_backend_t key_backend = {
        install_key, erase_key, state,
    };
    assert(openref_crew_session_init(crew, 0u, key_backend));
    openref_admission_config_t config = {100u, 500u, 3u};
    openref_admission_backend_t backend = {
        verify, unwrap, persist_counter, state,
    };
    openref_crew_admission_protocol_t protocol;
    assert(openref_crew_admission_init(
        &protocol, &config, backend, crew, counter, 0u));
    return protocol;
}

static void test_authenticated_invitation_activates_dynamic_assignment(void)
{
    backend_state_t state = {
        .verify_ok = true, .unwrap_ok = true, .persist_ok = true,
        .install_ok = true,
    };
    openref_crew_session_t crew;
    openref_crew_admission_protocol_t protocol =
        make_protocol(&state, &crew, 10u);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES];
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];
    memset(challenge, 0x22, sizeof(challenge));
    make_invitation(wire, challenge, 11u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 1u));
    assert(openref_crew_admission_accept(&protocol, wire, 2u));
    assert(crew.active && crew.local_node_id == 2u);
    assert(crew.member_mask == 0x07u && state.installed_key == 0x66u);
    assert(state.persisted_counter == 11u);
}

static void test_replay_wrong_challenge_and_expiry_reject(void)
{
    backend_state_t state = {
        .verify_ok = true, .unwrap_ok = true, .persist_ok = true,
        .install_ok = true,
    };
    openref_crew_session_t crew;
    openref_crew_admission_protocol_t protocol =
        make_protocol(&state, &crew, 10u);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES];
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];
    memset(challenge, 0x22, sizeof(challenge));
    make_invitation(wire, challenge, 10u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 1u));
    assert(!openref_crew_admission_accept(&protocol, wire, 2u));
    make_invitation(wire, challenge, 11u);
    wire[16] ^= 1u;
    assert(openref_crew_admission_begin(&protocol, true, challenge, 3u));
    assert(!openref_crew_admission_accept(&protocol, wire, 4u));
    make_invitation(wire, challenge, 12u);
    assert(openref_crew_admission_begin(&protocol, true, challenge, 5u));
    assert(!openref_crew_admission_accept(&protocol, wire, 106u));
    assert(!openref_crew_admission_begin(&protocol, true, challenge, 107u));
    assert(openref_crew_admission_begin(&protocol, true, challenge, 606u));
}

static void test_crypto_persistence_and_physical_presence_fail_closed(void)
{
    backend_state_t state = {
        .verify_ok = false, .unwrap_ok = true, .persist_ok = true,
        .install_ok = true,
    };
    openref_crew_session_t crew;
    openref_crew_admission_protocol_t protocol =
        make_protocol(&state, &crew, 0u);
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES];
    uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES];
    memset(challenge, 0x22, sizeof(challenge));
    make_invitation(wire, challenge, 1u);
    assert(!openref_crew_admission_begin(&protocol, false, challenge, 1u));
    assert(openref_crew_admission_begin(&protocol, true, challenge, 2u));
    assert(!openref_crew_admission_accept(&protocol, wire, 3u));
    state.verify_ok = true;
    state.persist_ok = false;
    assert(openref_crew_admission_begin(&protocol, true, challenge, 4u));
    assert(!openref_crew_admission_accept(&protocol, wire, 5u));
    assert(!crew.active);
}

int main(void)
{
    test_authenticated_invitation_activates_dynamic_assignment();
    test_replay_wrong_challenge_and_expiry_reject();
    test_crypto_persistence_and_physical_presence_fail_closed();
    return 0;
}
