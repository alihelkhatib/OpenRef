#include "openref_proto0_packet.h"

#include <stdbool.h>
#include <stddef.h>

static void write_u16_le(uint8_t *buffer, uint16_t value)
{
    buffer[0] = (uint8_t)(value & 0xffu);
    buffer[1] = (uint8_t)((value >> 8) & 0xffu);
}

static void write_u64_le(uint8_t *buffer, uint64_t value)
{
    for (uint8_t index = 0; index < 8u; index++) {
        buffer[index] = (uint8_t)((value >> (index * 8u)) & 0xffu);
    }
}

static uint16_t read_u16_le(const uint8_t *buffer)
{
    return (uint16_t)buffer[0] | ((uint16_t)buffer[1] << 8);
}

static uint64_t read_u64_le(const uint8_t *buffer)
{
    uint64_t value = 0u;
    for (uint8_t index = 0; index < 8u; index++) {
        value |= ((uint64_t)buffer[index]) << (index * 8u);
    }
    return value;
}

uint16_t openref_proto0_packet_length(uint16_t payload_length)
{
    if (payload_length > OPENREF_PROTO0_MAX_PAYLOAD_BYTES) {
        return 0u;
    }
    return (uint16_t)(OPENREF_PROTO0_HEADER_BYTES + payload_length);
}

bool openref_proto0_encode_header(
    const openref_proto0_packet_header_t *header,
    uint8_t *buffer,
    uint16_t capacity)
{
    if (header == NULL || buffer == NULL || capacity < OPENREF_PROTO0_HEADER_BYTES) {
        return false;
    }
    if (header->magic != OPENREF_PROTO0_MAGIC ||
        header->version != OPENREF_PROTO0_PACKET_VERSION ||
        header->payload_length > OPENREF_PROTO0_MAX_PAYLOAD_BYTES) {
        return false;
    }

    write_u16_le(&buffer[0], header->magic);
    buffer[2] = header->version;
    buffer[3] = header->kind;
    buffer[4] = header->source_id;
    buffer[5] = header->destination_id;
    write_u16_le(&buffer[6], header->sequence);
    write_u64_le(&buffer[8], header->tx_timestamp_us);
    write_u16_le(&buffer[16], header->payload_length);
    return true;
}

bool openref_proto0_decode_header(
    const uint8_t *buffer,
    uint16_t length,
    openref_proto0_packet_header_t *header)
{
    if (buffer == NULL || header == NULL || length < OPENREF_PROTO0_HEADER_BYTES) {
        return false;
    }

    header->magic = read_u16_le(&buffer[0]);
    header->version = buffer[2];
    header->kind = buffer[3];
    header->source_id = buffer[4];
    header->destination_id = buffer[5];
    header->sequence = read_u16_le(&buffer[6]);
    header->tx_timestamp_us = read_u64_le(&buffer[8]);
    header->payload_length = read_u16_le(&buffer[16]);

    if (header->magic != OPENREF_PROTO0_MAGIC ||
        header->version != OPENREF_PROTO0_PACKET_VERSION ||
        header->payload_length > OPENREF_PROTO0_MAX_PAYLOAD_BYTES) {
        return false;
    }
    return length >= openref_proto0_packet_length(header->payload_length);
}
