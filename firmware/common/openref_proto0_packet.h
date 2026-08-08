#ifndef OPENREF_PROTO0_PACKET_H
#define OPENREF_PROTO0_PACKET_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_PROTO0_MAGIC 0x4F52u
#define OPENREF_PROTO0_PACKET_VERSION 1u
#define OPENREF_PROTO0_MAX_PAYLOAD_BYTES 255u
#define OPENREF_PROTO0_HEADER_BYTES 18u

typedef enum {
    OPENREF_PROTO0_PACKET_PING = 1,
    OPENREF_PROTO0_PACKET_AUDIO_FRAME = 2,
    OPENREF_PROTO0_PACKET_HEARTBEAT = 3,
    OPENREF_PROTO0_PACKET_CONTROL = 4
} openref_proto0_packet_kind_t;

typedef struct {
    uint16_t magic;
    uint8_t version;
    uint8_t kind;
    uint8_t source_id;
    uint8_t destination_id;
    uint16_t sequence;
    uint64_t tx_timestamp_us;
    uint16_t payload_length;
} openref_proto0_packet_header_t;

bool openref_proto0_encode_header(
    const openref_proto0_packet_header_t *header,
    uint8_t *buffer,
    uint16_t capacity);

bool openref_proto0_decode_header(
    const uint8_t *buffer,
    uint16_t length,
    openref_proto0_packet_header_t *header);

uint16_t openref_proto0_packet_length(uint16_t payload_length);

#ifdef __cplusplus
}
#endif

#endif
