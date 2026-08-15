#ifndef OPENREF_DIAGNOSTICS_H
#define OPENREF_DIAGNOSTICS_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_DIAGNOSTIC_CAPACITY 32u
#define OPENREF_DIAGNOSTIC_WIRE_BYTES 16u

typedef enum {
    OPENREF_DIAGNOSTIC_INFO = 0,
    OPENREF_DIAGNOSTIC_WARNING = 1,
    OPENREF_DIAGNOSTIC_ERROR = 2,
    OPENREF_DIAGNOSTIC_FATAL = 3
} openref_diagnostic_severity_t;

typedef enum {
    OPENREF_EVENT_BOOT = 1,
    OPENREF_EVENT_RADIO_JOINED = 2,
    OPENREF_EVENT_RADIO_COORDINATOR_CHANGED = 3,
    OPENREF_EVENT_RADIO_AUTH_FAILURE = 4,
    OPENREF_EVENT_RADIO_REPLAY_REJECTED = 5,
    OPENREF_EVENT_AUDIO_DEADLINE_MISS = 16,
    OPENREF_EVENT_AUDIO_CAPTURE_GAP = 17,
    OPENREF_EVENT_AUDIO_QUEUE_OVERRUN = 18,
    OPENREF_EVENT_POWER_LOW = 32,
    OPENREF_EVENT_POWER_CRITICAL = 33,
    OPENREF_EVENT_POWER_SHUTDOWN = 34,
    OPENREF_EVENT_POWER_OVERTEMPERATURE = 35,
    OPENREF_EVENT_PEER_RESET = 48,
    OPENREF_EVENT_PEER_POWER_CYCLE = 49,
    OPENREF_EVENT_PEER_FAILED = 50,
    OPENREF_EVENT_ASSERTION = 64,
    OPENREF_EVENT_WATCHDOG_WITHHELD = 65,
    OPENREF_EVENT_STARTUP_FAULT = 66,
    OPENREF_EVENT_ACCESSORY_STATE = 67,
    OPENREF_EVENT_CHARGE_STATE = 68,
    OPENREF_EVENT_UPDATE_REJECTED = 69,
    OPENREF_EVENT_SERVICE_AUTH_FAILURE = 70
} openref_diagnostic_event_code_t;

typedef struct {
    uint64_t timestamp_ms;
    uint32_t value;
    uint16_t code;
    uint8_t source_id;
    uint8_t severity;
} openref_diagnostic_event_t;

typedef struct {
    openref_diagnostic_event_t events[OPENREF_DIAGNOSTIC_CAPACITY];
    uint8_t head;
    uint8_t count;
    uint32_t recorded;
    uint32_t overwritten;
} openref_diagnostics_t;

void openref_diagnostics_init(openref_diagnostics_t *diagnostics);

bool openref_diagnostics_record(
    openref_diagnostics_t *diagnostics,
    uint64_t timestamp_ms,
    openref_diagnostic_event_code_t code,
    openref_diagnostic_severity_t severity,
    uint8_t source_id,
    uint32_t value);

bool openref_diagnostics_pop(
    openref_diagnostics_t *diagnostics,
    openref_diagnostic_event_t *event);

bool openref_diagnostics_peek(
    const openref_diagnostics_t *diagnostics,
    uint8_t chronological_index,
    openref_diagnostic_event_t *event);

bool openref_diagnostic_encode(
    const openref_diagnostic_event_t *event,
    uint8_t wire[OPENREF_DIAGNOSTIC_WIRE_BYTES]);

bool openref_diagnostic_decode(
    const uint8_t wire[OPENREF_DIAGNOSTIC_WIRE_BYTES],
    openref_diagnostic_event_t *event);

#endif
