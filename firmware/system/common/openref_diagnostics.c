#include "openref_diagnostics.h"

#include <stddef.h>

static void write_u32_le(uint8_t *buffer, uint32_t value)
{
    for (uint8_t index = 0u; index < 4u; index++) {
        buffer[index] = (uint8_t)(value >> (index * 8u));
    }
}

static uint32_t read_u32_le(const uint8_t *buffer)
{
    uint32_t value = 0u;
    for (uint8_t index = 0u; index < 4u; index++) {
        value |= (uint32_t)buffer[index] << (index * 8u);
    }
    return value;
}

static void write_u64_le(uint8_t *buffer, uint64_t value)
{
    for (uint8_t index = 0u; index < 8u; index++) {
        buffer[index] = (uint8_t)(value >> (index * 8u));
    }
}

static uint64_t read_u64_le(const uint8_t *buffer)
{
    uint64_t value = 0u;
    for (uint8_t index = 0u; index < 8u; index++) {
        value |= (uint64_t)buffer[index] << (index * 8u);
    }
    return value;
}

void openref_diagnostics_init(openref_diagnostics_t *diagnostics)
{
    if (diagnostics != NULL) {
        *diagnostics = (openref_diagnostics_t){0};
    }
}

bool openref_diagnostics_record(
    openref_diagnostics_t *diagnostics,
    uint64_t timestamp_ms,
    openref_diagnostic_event_code_t code,
    openref_diagnostic_severity_t severity,
    uint8_t source_id,
    uint32_t value)
{
    if (diagnostics == NULL || code == 0 || severity > OPENREF_DIAGNOSTIC_FATAL) {
        return false;
    }
    if (diagnostics->count == OPENREF_DIAGNOSTIC_CAPACITY) {
        diagnostics->head = (uint8_t)(
            (diagnostics->head + 1u) % OPENREF_DIAGNOSTIC_CAPACITY);
        diagnostics->count--;
        diagnostics->overwritten++;
    }
    uint8_t tail = (uint8_t)(
        (diagnostics->head + diagnostics->count) % OPENREF_DIAGNOSTIC_CAPACITY);
    diagnostics->events[tail] = (openref_diagnostic_event_t){
        .timestamp_ms = timestamp_ms,
        .value = value,
        .code = (uint16_t)code,
        .source_id = source_id,
        .severity = (uint8_t)severity,
    };
    diagnostics->count++;
    diagnostics->recorded++;
    return true;
}

bool openref_diagnostics_pop(
    openref_diagnostics_t *diagnostics,
    openref_diagnostic_event_t *event)
{
    if (diagnostics == NULL || event == NULL || diagnostics->count == 0u) {
        return false;
    }
    *event = diagnostics->events[diagnostics->head];
    diagnostics->head = (uint8_t)(
        (diagnostics->head + 1u) % OPENREF_DIAGNOSTIC_CAPACITY);
    diagnostics->count--;
    return true;
}

bool openref_diagnostics_peek(
    const openref_diagnostics_t *diagnostics,
    uint8_t chronological_index,
    openref_diagnostic_event_t *event)
{
    if (diagnostics == NULL || event == NULL ||
        chronological_index >= diagnostics->count) {
        return false;
    }
    uint8_t index = (uint8_t)(
        (diagnostics->head + chronological_index) % OPENREF_DIAGNOSTIC_CAPACITY);
    *event = diagnostics->events[index];
    return true;
}

bool openref_diagnostic_encode(
    const openref_diagnostic_event_t *event,
    uint8_t wire[OPENREF_DIAGNOSTIC_WIRE_BYTES])
{
    if (event == NULL || wire == NULL || event->code == 0u ||
        event->severity > OPENREF_DIAGNOSTIC_FATAL) {
        return false;
    }
    write_u64_le(&wire[0], event->timestamp_ms);
    write_u32_le(&wire[8], event->value);
    wire[12] = (uint8_t)(event->code & 0xffu);
    wire[13] = (uint8_t)(event->code >> 8u);
    wire[14] = event->source_id;
    wire[15] = event->severity;
    return true;
}

bool openref_diagnostic_decode(
    const uint8_t wire[OPENREF_DIAGNOSTIC_WIRE_BYTES],
    openref_diagnostic_event_t *event)
{
    if (wire == NULL || event == NULL) {
        return false;
    }
    uint16_t code = (uint16_t)wire[12] | ((uint16_t)wire[13] << 8u);
    if (code == 0u || wire[15] > OPENREF_DIAGNOSTIC_FATAL) {
        return false;
    }
    *event = (openref_diagnostic_event_t){
        .timestamp_ms = read_u64_le(&wire[0]),
        .value = read_u32_le(&wire[8]),
        .code = code,
        .source_id = wire[14],
        .severity = wire[15],
    };
    return true;
}
