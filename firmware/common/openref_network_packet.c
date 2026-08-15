#include "openref_network_packet.h"

#include <stddef.h>
#include <string.h>

static void write_u32_le(uint8_t *buffer, uint32_t value)
{
    for (uint8_t index = 0u; index < 4u; index++) {
        buffer[index] = (uint8_t)((value >> (index * 8u)) & 0xffu);
    }
}

static void write_u64_le(uint8_t *buffer, uint64_t value)
{
    for (uint8_t index = 0u; index < 8u; index++) {
        buffer[index] = (uint8_t)((value >> (index * 8u)) & 0xffu);
    }
}

static uint32_t read_u32_le(const uint8_t *buffer)
{
    uint32_t value = 0u;
    for (uint8_t index = 0u; index < 4u; index++) {
        value |= ((uint32_t)buffer[index]) << (index * 8u);
    }
    return value;
}

static uint64_t read_u64_le(const uint8_t *buffer)
{
    uint64_t value = 0u;
    for (uint8_t index = 0u; index < 8u; index++) {
        value |= ((uint64_t)buffer[index]) << (index * 8u);
    }
    return value;
}

static bool valid_source(uint8_t source_id)
{
    return source_id >= 1u && source_id <= 6u;
}

static uint16_t initialize_packet(
    uint8_t kind,
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    uint8_t *packet,
    uint16_t capacity)
{
    if (packet == NULL || capacity < OPENREF_NETWORK_PACKET_BYTES ||
        !valid_source(source_id)) {
        return 0u;
    }
    openref_proto0_packet_header_t header = {
        .magic = OPENREF_PROTO0_MAGIC,
        .version = OPENREF_PROTO0_PACKET_VERSION,
        .kind = kind,
        .source_id = source_id,
        .destination_id = 0u,
        .sequence = sequence,
        .tx_timestamp_us = tx_timestamp_us,
        .payload_length = OPENREF_NETWORK_PAYLOAD_BYTES,
    };
    if (!openref_proto0_encode_header(&header, packet, capacity)) {
        return 0u;
    }
    memset(&packet[OPENREF_PROTO0_HEADER_BYTES], 0, OPENREF_NETWORK_PAYLOAD_BYTES);
    return OPENREF_NETWORK_PACKET_BYTES;
}

uint16_t openref_network_build_audio_packet(
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    uint8_t *packet,
    uint16_t capacity)
{
    uint16_t length = initialize_packet(
        OPENREF_PROTO0_PACKET_AUDIO_FRAME,
        source_id,
        sequence,
        tx_timestamp_us,
        packet,
        capacity);
    if (length == 0u) {
        return 0u;
    }
    for (uint16_t index = 0u; index < OPENREF_NETWORK_PAYLOAD_BYTES; index++) {
        packet[OPENREF_PROTO0_HEADER_BYTES + index] =
            (uint8_t)((sequence + index) & 0xffu);
    }
    return length;
}

uint16_t openref_network_build_audio_packet_with_payload(
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    const uint8_t payload[OPENREF_NETWORK_PAYLOAD_BYTES],
    uint8_t *packet,
    uint16_t capacity)
{
    if (payload == NULL) {
        return 0u;
    }
    uint16_t length = initialize_packet(
        OPENREF_PROTO0_PACKET_AUDIO_FRAME,
        source_id,
        sequence,
        tx_timestamp_us,
        packet,
        capacity);
    if (length == 0u) {
        return 0u;
    }
    memcpy(&packet[OPENREF_PROTO0_HEADER_BYTES], payload,
           OPENREF_NETWORK_PAYLOAD_BYTES);
    return length;
}

uint16_t openref_network_build_heartbeat_packet(
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    const openref_network_heartbeat_t *heartbeat,
    uint8_t *packet,
    uint16_t capacity)
{
    if (heartbeat == NULL) {
        return 0u;
    }
    uint16_t length = initialize_packet(
        OPENREF_PROTO0_PACKET_HEARTBEAT,
        source_id,
        sequence,
        tx_timestamp_us,
        packet,
        capacity);
    if (length == 0u) {
        return 0u;
    }
    uint8_t *payload = &packet[OPENREF_PROTO0_HEADER_BYTES];
    write_u32_le(payload, heartbeat->coordinator_epoch);
    write_u64_le(&payload[4], heartbeat->schedule_origin_us);
    return length;
}

bool openref_network_parse_packet(
    const uint8_t *packet,
    uint16_t length,
    openref_proto0_packet_header_t *header)
{
    if (packet == NULL || header == NULL || length != OPENREF_NETWORK_PACKET_BYTES ||
        !openref_proto0_decode_header(packet, length, header)) {
        return false;
    }
    return valid_source(header->source_id) && header->destination_id == 0u &&
        header->payload_length == OPENREF_NETWORK_PAYLOAD_BYTES &&
        (header->kind == OPENREF_PROTO0_PACKET_AUDIO_FRAME ||
         header->kind == OPENREF_PROTO0_PACKET_HEARTBEAT ||
         header->kind == OPENREF_PROTO0_PACKET_CONTROL);
}

bool openref_network_parse_heartbeat(
    const uint8_t *packet,
    uint16_t length,
    openref_network_heartbeat_t *heartbeat)
{
    openref_proto0_packet_header_t header;
    if (heartbeat == NULL || !openref_network_parse_packet(packet, length, &header) ||
        header.kind != OPENREF_PROTO0_PACKET_HEARTBEAT) {
        return false;
    }
    const uint8_t *payload = &packet[OPENREF_PROTO0_HEADER_BYTES];
    heartbeat->coordinator_epoch = read_u32_le(payload);
    heartbeat->schedule_origin_us = read_u64_le(&payload[4]);
    return true;
}
