#ifndef OPENREF_CREW_ADMISSION_H
#define OPENREF_CREW_ADMISSION_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_crew_session.h"

#define OPENREF_ADMISSION_WIRE_BYTES 168u
#define OPENREF_ADMISSION_SIGNED_BYTES 104u
#define OPENREF_ADMISSION_CHALLENGE_BYTES 32u
#define OPENREF_ADMISSION_WRAPPED_KEY_BYTES 32u
#define OPENREF_ADMISSION_SIGNATURE_BYTES 64u

typedef bool (*openref_admission_verify_fn)(
    void *context,
    const uint8_t signed_data[OPENREF_ADMISSION_SIGNED_BYTES],
    const uint8_t coordinator_fingerprint[8],
    const uint8_t signature[OPENREF_ADMISSION_SIGNATURE_BYTES]);
typedef bool (*openref_admission_unwrap_fn)(
    void *context,
    const uint8_t wrapped_key[OPENREF_ADMISSION_WRAPPED_KEY_BYTES],
    const uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES],
    uint32_t session_id,
    uint8_t session_key[OPENREF_CREW_SESSION_KEY_BYTES]);
typedef bool (*openref_admission_persist_counter_fn)(
    void *context, uint32_t counter);

typedef struct {
    openref_admission_verify_fn verify;
    openref_admission_unwrap_fn unwrap;
    openref_admission_persist_counter_fn persist_counter;
    void *context;
} openref_admission_backend_t;

typedef struct {
    uint32_t invitation_window_ms;
    uint32_t lockout_ms;
    uint8_t maximum_failures;
} openref_admission_config_t;

typedef struct {
    openref_admission_config_t config;
    openref_admission_backend_t backend;
    openref_crew_session_t *crew_session;
    uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES];
    uint64_t invitation_started_ms;
    uint64_t locked_until_ms;
    uint64_t last_time_ms;
    uint32_t last_admission_counter;
    uint32_t accepted_invitations;
    uint32_t rejected_invitations;
    uint8_t consecutive_failures;
    bool invitation_open;
} openref_crew_admission_protocol_t;

bool openref_crew_admission_init(
    openref_crew_admission_protocol_t *protocol,
    const openref_admission_config_t *config,
    openref_admission_backend_t backend,
    openref_crew_session_t *crew_session,
    uint32_t persisted_counter,
    uint64_t now_ms);

bool openref_crew_admission_begin(
    openref_crew_admission_protocol_t *protocol,
    bool physical_join_confirmed,
    const uint8_t challenge[OPENREF_ADMISSION_CHALLENGE_BYTES],
    uint64_t now_ms);

bool openref_crew_admission_accept(
    openref_crew_admission_protocol_t *protocol,
    const uint8_t invitation[OPENREF_ADMISSION_WIRE_BYTES],
    uint64_t now_ms);

void openref_crew_admission_cancel(
    openref_crew_admission_protocol_t *protocol);

#endif
