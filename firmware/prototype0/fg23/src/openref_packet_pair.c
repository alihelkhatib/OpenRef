#include "openref_packet_pair.h"

#include <stddef.h>

void openref_packet_pair_init_state(openref_packet_pair_state_t *state)
{
    if (state == NULL) {
        return;
    }
    state->sequence = 0u;
    state->tx_done_count = 0u;
    state->rx_done_count = 0u;
    state->rx_gap_count = 0u;
    state->fault_count = 0u;
    state->next_expected_rx_sequence = 0u;
    state->has_expected_rx_sequence = false;
}

uint16_t openref_packet_pair_build_ping(
    openref_packet_pair_state_t *state,
    uint8_t source_id,
    uint8_t destination_id,
    uint64_t timestamp_us,
    uint8_t *packet,
    uint16_t capacity)
{
    return openref_packet_pair_build_ping_with_payload(
        state,
        source_id,
        destination_id,
        timestamp_us,
        OPENREF_PACKET_PAIR_PAYLOAD_BYTES,
        packet,
        capacity);
}

uint16_t openref_packet_pair_build_ping_with_payload(
    openref_packet_pair_state_t *state,
    uint8_t source_id,
    uint8_t destination_id,
    uint64_t timestamp_us,
    uint16_t payload_bytes,
    uint8_t *packet,
    uint16_t capacity)
{
    if (state == NULL || packet == NULL ||
        payload_bytes > OPENREF_PROTO0_MAX_PAYLOAD_BYTES) {
        return 0u;
    }

    uint16_t packet_length = openref_proto0_packet_length(payload_bytes);
    if (packet_length == 0u || capacity < packet_length) {
        return 0u;
    }

    state->sequence++;
    openref_proto0_packet_header_t header = {
        .magic = OPENREF_PROTO0_MAGIC,
        .version = OPENREF_PROTO0_PACKET_VERSION,
        .kind = OPENREF_PROTO0_PACKET_PING,
        .source_id = source_id,
        .destination_id = destination_id,
        .sequence = state->sequence,
        .tx_timestamp_us = timestamp_us,
        .payload_length = payload_bytes,
    };

    if (!openref_proto0_encode_header(&header, packet, capacity)) {
        return 0u;
    }

    for (uint16_t index = 0u; index < payload_bytes; index++) {
        packet[OPENREF_PROTO0_HEADER_BYTES + index] =
            (uint8_t)((state->sequence + index) & 0xffu);
    }

    return packet_length;
}

bool openref_packet_pair_parse_rx(
    openref_packet_pair_state_t *state,
    const uint8_t *packet,
    uint16_t length,
    openref_proto0_packet_header_t *header,
    bool *gap_detected,
    uint16_t *expected_sequence)
{
    if (state == NULL || packet == NULL || header == NULL ||
        gap_detected == NULL || expected_sequence == NULL) {
        return false;
    }

    *gap_detected = false;
    *expected_sequence = 0u;
    if (!openref_proto0_decode_header(packet, length, header)) {
        state->fault_count++;
        return false;
    }

    if (header->kind != OPENREF_PROTO0_PACKET_PING) {
        state->fault_count++;
        return false;
    }

    if (state->has_expected_rx_sequence &&
        header->sequence != state->next_expected_rx_sequence) {
        *gap_detected = true;
        *expected_sequence = state->next_expected_rx_sequence;
        state->rx_gap_count++;
    }

    state->next_expected_rx_sequence = (uint16_t)(header->sequence + 1u);
    state->has_expected_rx_sequence = true;
    state->rx_done_count++;
    return true;
}
