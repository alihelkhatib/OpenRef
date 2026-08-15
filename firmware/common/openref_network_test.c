#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "openref_network.h"
#include "openref_network_packet.h"

typedef struct {
    bool succeed;
    uint32_t next_epoch;
    uint32_t calls;
} epoch_backend_t;

static bool advance_epoch(void *context, uint32_t current, uint32_t *next)
{
    epoch_backend_t *backend = context;
    backend->calls++;
    *next = backend->next_epoch;
    return backend->succeed && backend->next_epoch > current;
}

static void test_slot_calculation(void)
{
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(4u);
    assert(openref_network_init(&state, &config, 1000u));
    uint64_t slot_us = 0u;
    assert(openref_network_next_slot_us(&state, 1000u, &slot_us));
    assert(slot_us == 8500u);
    assert(openref_network_next_slot_us(&state, 8501u, &slot_us));
    assert(slot_us == 28500u);
}

static void test_coordinator_failure_and_stale_return(void)
{
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(2u);
    assert(openref_network_init(&state, &config, 0u));
    uint32_t actions = openref_network_tick(&state, OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US + 1u);
    assert((actions & OPENREF_NETWORK_ACTION_COORDINATOR_TIMEOUT) != 0u);
    actions = openref_network_tick(
        &state, OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US + OPENREF_NETWORK_ELECTION_DELAY_US + 1u);
    assert((actions & OPENREF_NETWORK_ACTION_COORDINATOR_CHANGED) != 0u);
    assert((actions & OPENREF_NETWORK_ACTION_SEND_HEARTBEAT) != 0u);
    assert(state.coordinator_id == 2u);
    assert(state.coordinator_epoch == 1u);
    assert(!openref_network_receive_heartbeat(&state, 1u, 0u, 0u, 400000u));
}

static void test_persisted_epoch_required_before_election(void)
{
    epoch_backend_t backend = {.succeed = false, .next_epoch = 8u};
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(2u);
    config.initial_coordinator_epoch = 7u;
    config.require_persisted_epoch = true;
    config.advance_epoch = advance_epoch;
    config.epoch_context = &backend;
    assert(openref_network_init(&state, &config, 0u));
    openref_network_tick(&state, OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US + 1u);
    uint64_t election = OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US +
        OPENREF_NETWORK_ELECTION_DELAY_US + 1u;
    uint32_t actions = openref_network_tick(&state, election);
    assert((actions & OPENREF_NETWORK_ACTION_EPOCH_FAILURE) != 0u);
    assert(state.role == OPENREF_NETWORK_ELECTION);
    assert(state.coordinator_epoch == 7u && state.epoch_failures == 1u);
    backend.succeed = true;
    actions = openref_network_tick(
        &state, election + OPENREF_NETWORK_ELECTION_DELAY_US + 1u);
    assert((actions & OPENREF_NETWORK_ACTION_COORDINATOR_CHANGED) != 0u);
    assert(state.coordinator_epoch == 8u && state.coordinator_id == 2u);
    assert(backend.calls == 2u);
}

static void test_epoch_exhaustion_fails_closed(void)
{
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(2u);
    config.initial_coordinator_epoch = UINT32_MAX;
    assert(openref_network_init(&state, &config, 0u));
    openref_network_tick(&state, OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US + 1u);
    uint32_t actions = openref_network_tick(&state,
        OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US +
        OPENREF_NETWORK_ELECTION_DELAY_US + 1u);
    assert((actions & OPENREF_NETWORK_ACTION_EPOCH_FAILURE) != 0u);
    assert(state.role == OPENREF_NETWORK_ELECTION);
}

static void test_same_epoch_tie_selects_lowest_coordinator(void)
{
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(3u);
    config.initial_coordinator_id = 2u;
    config.initial_coordinator_epoch = 5u;
    assert(openref_network_init(&state, &config, 0u));
    assert(!openref_network_receive_heartbeat(&state, 3u, 5u, 0u, 1u));
    assert(openref_network_receive_heartbeat(&state, 1u, 5u, 0u, 2u));
    assert(state.coordinator_id == 1u);
    assert(!openref_network_receive_heartbeat(&state, 2u, 5u, 0u, 3u));
}

static void test_sequence_tracking_and_wrap(void)
{
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(1u);
    uint16_t missing = 0u;
    assert(openref_network_init(&state, &config, 0u));
    assert(openref_network_receive_audio(&state, 2u, 65534u, &missing) == OPENREF_NETWORK_RX_FIRST);
    assert(openref_network_receive_audio(&state, 2u, 65535u, &missing) == OPENREF_NETWORK_RX_IN_ORDER);
    assert(openref_network_receive_audio(&state, 2u, 0u, &missing) == OPENREF_NETWORK_RX_IN_ORDER);
    assert(openref_network_receive_audio(&state, 2u, 2u, &missing) == OPENREF_NETWORK_RX_GAP);
    assert(missing == 1u);
    assert(openref_network_receive_audio(&state, 2u, 2u, &missing) == OPENREF_NETWORK_RX_DUPLICATE);
    assert(openref_network_receive_audio(&state, 2u, 1u, &missing) == OPENREF_NETWORK_RX_STALE);
}

static void test_reboot_sequence_is_accepted(void)
{
    openref_network_state_t state;
    openref_network_config_t config = openref_network_default_config(1u);
    uint16_t missing = 0u;
    assert(openref_network_init(&state, &config, 0u));
    assert(openref_network_receive_audio_timestamped(
        &state, 2u, 500u, 900000u, &missing) == OPENREF_NETWORK_RX_FIRST);
    assert(openref_network_receive_audio_timestamped(
        &state, 2u, 501u, 920000u, &missing) == OPENREF_NETWORK_RX_IN_ORDER);
    assert(openref_network_receive_audio_timestamped(
        &state, 2u, 1u, 10000u, &missing) == OPENREF_NETWORK_RX_FIRST);
    assert(openref_network_receive_audio_timestamped(
        &state, 2u, 2u, 30000u, &missing) == OPENREF_NETWORK_RX_IN_ORDER);
}

static void test_network_packet_round_trip(void)
{
    uint8_t packet[OPENREF_NETWORK_PACKET_BYTES];
    openref_network_heartbeat_t expected = {
        .coordinator_epoch = 0x01020304u,
        .schedule_origin_us = UINT64_C(0x1112131415161718),
    };
    assert(openref_network_build_heartbeat_packet(
        2u, 0x1234u, UINT64_C(0x0102030405060708),
        &expected, packet, sizeof(packet)) == OPENREF_NETWORK_PACKET_BYTES);

    openref_proto0_packet_header_t header;
    assert(openref_network_parse_packet(packet, sizeof(packet), &header));
    assert(header.kind == OPENREF_PROTO0_PACKET_HEARTBEAT);
    assert(header.source_id == 2u);
    assert(header.sequence == 0x1234u);

    openref_network_heartbeat_t decoded;
    assert(openref_network_parse_heartbeat(packet, sizeof(packet), &decoded));
    assert(decoded.coordinator_epoch == expected.coordinator_epoch);
    assert(decoded.schedule_origin_us == expected.schedule_origin_us);
    assert(!openref_network_parse_packet(packet, sizeof(packet) - 1u, &header));
}

static void test_audio_payload_round_trip(void)
{
    uint8_t payload[OPENREF_NETWORK_PAYLOAD_BYTES];
    uint8_t packet[OPENREF_NETWORK_PACKET_BYTES];
    for (uint16_t index = 0u; index < sizeof(payload); index++) {
        payload[index] = (uint8_t)(index ^ 0x5au);
    }
    assert(openref_network_build_audio_packet_with_payload(
        3u, 42u, 123456u, payload, packet, sizeof(packet)) ==
        OPENREF_NETWORK_PACKET_BYTES);
    openref_proto0_packet_header_t header;
    assert(openref_network_parse_packet(packet, sizeof(packet), &header));
    assert(header.kind == OPENREF_PROTO0_PACKET_AUDIO_FRAME);
    assert(header.source_id == 3u);
    assert(header.sequence == 42u);
    for (uint16_t index = 0u; index < sizeof(payload); index++) {
        assert(packet[OPENREF_PROTO0_HEADER_BYTES + index] == payload[index]);
    }
    assert(openref_network_build_audio_packet_with_payload(
        3u, 42u, 123456u, NULL, packet, sizeof(packet)) == 0u);
}

int main(void)
{
    test_slot_calculation();
    test_coordinator_failure_and_stale_return();
    test_persisted_epoch_required_before_election();
    test_epoch_exhaustion_fails_closed();
    test_same_epoch_tie_selects_lowest_coordinator();
    test_sequence_tracking_and_wrap();
    test_reboot_sequence_is_accepted();
    test_network_packet_round_trip();
    test_audio_payload_round_trip();
    return 0;
}
