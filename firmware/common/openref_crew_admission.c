#include "openref_crew_admission.h"

#include <stddef.h>
#include <string.h>

static uint32_t read_u32(const uint8_t *data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8) |
        ((uint32_t)data[2] << 16) | ((uint32_t)data[3] << 24);
}

static bool nonzero(const uint8_t *data, uint8_t length)
{
    uint8_t aggregate = 0u;
    for (uint8_t i = 0u; i < length; i++) {
        aggregate |= data[i];
    }
    return aggregate != 0u;
}

static bool equal_constant_time(const uint8_t *left, const uint8_t *right,
                                uint8_t length)
{
    uint8_t difference = 0u;
    for (uint8_t i = 0u; i < length; i++) {
        difference |= (uint8_t)(left[i] ^ right[i]);
    }
    return difference == 0u;
}

static uint8_t population(uint8_t mask)
{
    uint8_t count = 0u;
    for (uint8_t bit = 0u; bit < OPENREF_CREW_MAX_MEMBERS; bit++) {
        count += (uint8_t)((mask >> bit) & 1u);
    }
    return count;
}

static uint64_t deadline(uint64_t now_ms, uint32_t duration_ms)
{
    return UINT64_MAX - now_ms < duration_ms
        ? UINT64_MAX : now_ms + duration_ms;
}

void openref_crew_admission_cancel(openref_crew_admission_protocol_t *protocol)
{
    if (protocol != NULL) {
        memset(protocol->challenge, 0, sizeof(protocol->challenge));
        protocol->invitation_open = false;
    }
}

static bool reject(openref_crew_admission_protocol_t *protocol,
                   uint64_t now_ms)
{
    protocol->rejected_invitations++;
    if (protocol->consecutive_failures < UINT8_MAX) {
        protocol->consecutive_failures++;
    }
    openref_crew_admission_cancel(protocol);
    if (protocol->consecutive_failures >= protocol->config.maximum_failures) {
        protocol->locked_until_ms = deadline(now_ms, protocol->config.lockout_ms);
    }
    return false;
}

static bool time_valid(openref_crew_admission_protocol_t *protocol,
                       uint64_t now_ms)
{
    if (now_ms < protocol->last_time_ms) {
        openref_crew_admission_cancel(protocol);
        protocol->rejected_invitations++;
        return false;
    }
    protocol->last_time_ms = now_ms;
    return true;
}

bool openref_crew_admission_init(openref_crew_admission_protocol_t *protocol,
    const openref_admission_config_t *config,
    openref_admission_backend_t backend, openref_crew_session_t *crew_session,
    uint32_t persisted_counter, uint64_t now_ms)
{
    if (protocol == NULL || config == NULL || crew_session == NULL ||
        config->invitation_window_ms == 0u || config->lockout_ms == 0u ||
        config->maximum_failures == 0u || backend.verify == NULL ||
        backend.unwrap == NULL || backend.persist_counter == NULL) {
        return false;
    }
    memset(protocol, 0, sizeof(*protocol));
    protocol->config = *config;
    protocol->backend = backend;
    protocol->crew_session = crew_session;
    protocol->last_admission_counter = persisted_counter;
    protocol->last_time_ms = now_ms;
    return true;
}

bool openref_crew_admission_begin(openref_crew_admission_protocol_t *protocol,
    bool physical_join_confirmed,
    const uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES], uint64_t now_ms)
{
    if (protocol == NULL || challenge == NULL ||
        !time_valid(protocol, now_ms) || now_ms < protocol->locked_until_ms ||
        !physical_join_confirmed || protocol->crew_session->active ||
        !nonzero(challenge, OPENREF_ADMISSION_CHALLENGE_BYTES)) {
        return false;
    }
    openref_crew_admission_cancel(protocol);
    memcpy(protocol->challenge, challenge, sizeof(protocol->challenge));
    protocol->invitation_started_ms = now_ms;
    protocol->invitation_open = true;
    return true;
}

bool openref_crew_admission_accept(openref_crew_admission_protocol_t *protocol,
    const uint8_t wire[OPENREF_ADMISSION_WIRE_BYTES], uint64_t now_ms)
{
    if (protocol == NULL || wire == NULL || !time_valid(protocol, now_ms)) {
        return false;
    }
    uint8_t local_node_id = wire[5];
    uint8_t member_mask = wire[6];
    uint8_t member_count = wire[7];
    uint32_t session_id = read_u32(&wire[8]);
    uint32_t counter = read_u32(&wire[12]);
    uint8_t local_bit = local_node_id >= 1u &&
        local_node_id <= OPENREF_CREW_MAX_MEMBERS
        ? (uint8_t)(1u << (local_node_id - 1u)) : 0u;
    bool valid = protocol->invitation_open && !protocol->crew_session->active &&
        now_ms - protocol->invitation_started_ms <=
            protocol->config.invitation_window_ms &&
        wire[0] == 0x4fu && wire[1] == 0x52u && wire[2] == 0x4au &&
        wire[3] == 0x4eu && wire[4] == 1u && local_bit != 0u &&
        (member_mask & 0xc0u) == 0u && (member_mask & local_bit) != 0u &&
        member_count >= 2u &&
        member_count <= OPENREF_CREW_MAX_MEMBERS &&
        population(member_mask) == member_count && session_id != 0u &&
        counter > protocol->last_admission_counter &&
        equal_constant_time(&wire[16], protocol->challenge,
                            OPENREF_ADMISSION_CHALLENGE_BYTES) &&
        nonzero(&wire[48], 8u) && nonzero(&wire[56], 16u) &&
        protocol->backend.verify(protocol->backend.context, wire, &wire[48],
            &wire[OPENREF_ADMISSION_SIGNED_BYTES]);
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES] = {0};
    if (!valid || !protocol->backend.unwrap(protocol->backend.context,
            &wire[72], protocol->challenge, session_id, key) ||
        !protocol->backend.persist_counter(protocol->backend.context, counter)) {
        memset(key, 0, sizeof(key));
        return reject(protocol, now_ms);
    }
    protocol->last_admission_counter = counter;
    openref_crew_admission_t admission = {
        .session_id = session_id,
        .member_mask = member_mask,
        .member_count = member_count,
        .local_node_id = local_node_id,
        .authenticated = true,
    };
    bool activated = openref_crew_session_activate(
        protocol->crew_session, &admission, key);
    memset(key, 0, sizeof(key));
    openref_crew_admission_cancel(protocol);
    if (!activated) {
        protocol->rejected_invitations++;
        return false;
    }
    protocol->consecutive_failures = 0u;
    protocol->accepted_invitations++;
    return true;
}
