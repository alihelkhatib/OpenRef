#include "openref_audio_link.h"

#include <stddef.h>
#include <string.h>

static void write_u16_le(uint8_t *buffer, uint16_t value)
{
    buffer[0] = (uint8_t)(value & 0xffu);
    buffer[1] = (uint8_t)(value >> 8);
}

static void write_u32_le(uint8_t *buffer, uint32_t value)
{
    for (uint8_t index = 0u; index < 4u; index++) {
        buffer[index] = (uint8_t)(value >> (index * 8u));
    }
}

static uint16_t read_u16_le(const uint8_t *buffer)
{
    return (uint16_t)buffer[0] | ((uint16_t)buffer[1] << 8);
}

static uint32_t read_u32_le(const uint8_t *buffer)
{
    uint32_t value = 0u;
    for (uint8_t index = 0u; index < 4u; index++) {
        value |= (uint32_t)buffer[index] << (index * 8u);
    }
    return value;
}

static bool valid_kind(uint8_t kind)
{
    return kind == OPENREF_AUDIO_LINK_LOCAL_AUDIO ||
        kind == OPENREF_AUDIO_LINK_REMOTE_AUDIO ||
        kind == OPENREF_AUDIO_LINK_STATUS;
}

static bool valid_frame(const openref_audio_link_frame_t *frame)
{
    if (frame == NULL || !valid_kind(frame->kind)) {
        return false;
    }
    if (frame->kind == OPENREF_AUDIO_LINK_STATUS) {
        return frame->source_id == 0u;
    }
    return frame->source_id >= 1u && frame->source_id <= 6u;
}

uint16_t openref_audio_link_crc16(const uint8_t *data, uint16_t length)
{
    if (data == NULL) {
        return 0u;
    }
    uint16_t crc = 0xffffu;
    for (uint16_t index = 0u; index < length; index++) {
        crc ^= (uint16_t)data[index] << 8;
        for (uint8_t bit = 0u; bit < 8u; bit++) {
            crc = (crc & 0x8000u) != 0u
                ? (uint16_t)((crc << 1) ^ 0x1021u)
                : (uint16_t)(crc << 1);
        }
    }
    return crc;
}

bool openref_audio_link_encode(
    const openref_audio_link_frame_t *frame,
    uint8_t *wire,
    uint16_t capacity)
{
    if (!valid_frame(frame) || wire == NULL ||
        capacity < OPENREF_AUDIO_LINK_FRAME_BYTES ||
        frame->producer_queue_depth > OPENREF_AUDIO_LINK_QUEUE_CAPACITY) {
        return false;
    }
    write_u16_le(&wire[0], OPENREF_AUDIO_LINK_MAGIC);
    wire[2] = OPENREF_AUDIO_LINK_VERSION;
    wire[3] = frame->kind;
    wire[4] = frame->source_id;
    wire[5] = frame->flags;
    write_u16_le(&wire[6], frame->sequence);
    write_u32_le(&wire[8], frame->timestamp_us);
    write_u16_le(&wire[12], OPENREF_AUDIO_LINK_PAYLOAD_BYTES);
    wire[14] = frame->producer_queue_depth;
    wire[15] = 0u;
    memcpy(&wire[OPENREF_AUDIO_LINK_HEADER_BYTES], frame->payload,
           OPENREF_AUDIO_LINK_PAYLOAD_BYTES);
    write_u16_le(&wire[OPENREF_AUDIO_LINK_HEADER_BYTES + OPENREF_AUDIO_LINK_PAYLOAD_BYTES],
                 openref_audio_link_crc16(wire, OPENREF_AUDIO_LINK_FRAME_BYTES - 2u));
    return true;
}

bool openref_audio_link_decode(
    const uint8_t *wire,
    uint16_t length,
    openref_audio_link_frame_t *frame)
{
    if (wire == NULL || frame == NULL || length != OPENREF_AUDIO_LINK_FRAME_BYTES ||
        read_u16_le(&wire[0]) != OPENREF_AUDIO_LINK_MAGIC ||
        wire[2] != OPENREF_AUDIO_LINK_VERSION || !valid_kind(wire[3]) ||
        read_u16_le(&wire[12]) != OPENREF_AUDIO_LINK_PAYLOAD_BYTES ||
        wire[14] > OPENREF_AUDIO_LINK_QUEUE_CAPACITY || wire[15] != 0u ||
        read_u16_le(&wire[length - 2u]) != openref_audio_link_crc16(wire, length - 2u)) {
        return false;
    }
    frame->kind = wire[3];
    frame->source_id = wire[4];
    frame->flags = wire[5];
    frame->sequence = read_u16_le(&wire[6]);
    frame->timestamp_us = read_u32_le(&wire[8]);
    frame->producer_queue_depth = wire[14];
    memcpy(frame->payload, &wire[OPENREF_AUDIO_LINK_HEADER_BYTES],
           OPENREF_AUDIO_LINK_PAYLOAD_BYTES);
    return valid_frame(frame);
}

void openref_audio_link_queue_init(openref_audio_link_queue_t *queue)
{
    if (queue != NULL) {
        memset(queue, 0, sizeof(*queue));
    }
}

bool openref_audio_link_queue_push(
    openref_audio_link_queue_t *queue,
    const openref_audio_link_frame_t *frame)
{
    if (queue == NULL || !valid_frame(frame)) {
        return false;
    }
    if (queue->count == OPENREF_AUDIO_LINK_QUEUE_CAPACITY) {
        queue->head = (uint8_t)((queue->head + 1u) % OPENREF_AUDIO_LINK_QUEUE_CAPACITY);
        queue->count--;
        queue->overruns++;
    }
    uint8_t tail = (uint8_t)((queue->head + queue->count) %
                             OPENREF_AUDIO_LINK_QUEUE_CAPACITY);
    queue->entries[tail] = *frame;
    queue->count++;
    queue->pushes++;
    return true;
}

bool openref_audio_link_queue_pop(
    openref_audio_link_queue_t *queue,
    openref_audio_link_frame_t *frame)
{
    if (queue == NULL || frame == NULL || queue->count == 0u) {
        return false;
    }
    *frame = queue->entries[queue->head];
    queue->head = (uint8_t)((queue->head + 1u) % OPENREF_AUDIO_LINK_QUEUE_CAPACITY);
    queue->count--;
    queue->pops++;
    return true;
}
