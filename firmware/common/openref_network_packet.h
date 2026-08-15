#ifndef OPENREF_NETWORK_PACKET_H
#define OPENREF_NETWORK_PACKET_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_proto0_packet.h"

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_NETWORK_PAYLOAD_BYTES 80u
#define OPENREF_NETWORK_PACKET_BYTES \
    (OPENREF_PROTO0_HEADER_BYTES + OPENREF_NETWORK_PAYLOAD_BYTES)
#define OPENREF_NETWORK_HEARTBEAT_BODY_BYTES 12u

typedef struct {
    uint32_t coordinator_epoch;
    uint64_t schedule_origin_us;
} openref_network_heartbeat_t;

uint16_t openref_network_build_audio_packet(
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    uint8_t *packet,
    uint16_t capacity);

uint16_t openref_network_build_audio_packet_with_payload(
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    const uint8_t payload[OPENREF_NETWORK_PAYLOAD_BYTES],
    uint8_t *packet,
    uint16_t capacity);

uint16_t openref_network_build_heartbeat_packet(
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    const openref_network_heartbeat_t *heartbeat,
    uint8_t *packet,
    uint16_t capacity);

bool openref_network_parse_packet(
    const uint8_t *packet,
    uint16_t length,
    openref_proto0_packet_header_t *header);

bool openref_network_parse_heartbeat(
    const uint8_t *packet,
    uint16_t length,
    openref_network_heartbeat_t *heartbeat);

#ifdef __cplusplus
}
#endif

#endif
