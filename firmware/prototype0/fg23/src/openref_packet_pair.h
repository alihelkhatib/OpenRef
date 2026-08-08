#ifndef OPENREF_PACKET_PAIR_H
#define OPENREF_PACKET_PAIR_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_proto0_packet.h"
#include "openref_radio.h"

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_PACKET_PAIR_TX_NODE_ID 1u
#define OPENREF_PACKET_PAIR_RX_NODE_ID 2u
#define OPENREF_PACKET_PAIR_PAYLOAD_BYTES 60u
#define OPENREF_PACKET_PAIR_INTERVAL_US 20000u
#define OPENREF_PACKET_PAIR_MAX_PACKET_BYTES \
    (OPENREF_PROTO0_HEADER_BYTES + OPENREF_PROTO0_MAX_PAYLOAD_BYTES)

typedef enum {
    OPENREF_PACKET_PAIR_ROLE_TX = 1,
    OPENREF_PACKET_PAIR_ROLE_RX = 2
} openref_packet_pair_role_t;

typedef struct {
    uint16_t sequence;
    uint32_t tx_done_count;
    uint32_t rx_done_count;
    uint32_t rx_gap_count;
    uint32_t fault_count;
    uint16_t next_expected_rx_sequence;
    bool has_expected_rx_sequence;
} openref_packet_pair_state_t;

void openref_packet_pair_init_state(openref_packet_pair_state_t *state);

uint16_t openref_packet_pair_build_ping(
    openref_packet_pair_state_t *state,
    uint8_t source_id,
    uint8_t destination_id,
    uint64_t timestamp_us,
    uint8_t *packet,
    uint16_t capacity);

uint16_t openref_packet_pair_build_ping_with_payload(
    openref_packet_pair_state_t *state,
    uint8_t source_id,
    uint8_t destination_id,
    uint64_t timestamp_us,
    uint16_t payload_bytes,
    uint8_t *packet,
    uint16_t capacity);

bool openref_packet_pair_parse_rx(
    openref_packet_pair_state_t *state,
    const uint8_t *packet,
    uint16_t length,
    openref_proto0_packet_header_t *header,
    bool *gap_detected,
    uint16_t *expected_sequence);

#ifdef __cplusplus
}
#endif

#endif
