#ifndef OPENREF_SERVICE_SESSION_H
#define OPENREF_SERVICE_SESSION_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_SERVICE_CHALLENGE_BYTES 32u
#define OPENREF_SERVICE_RESPONSE_BYTES 32u

#define OPENREF_SERVICE_PERMISSION_DIAGNOSTICS (1u << 0)
#define OPENREF_SERVICE_PERMISSION_CONFIG_READ (1u << 1)
#define OPENREF_SERVICE_PERMISSION_CONFIG_WRITE (1u << 2)
#define OPENREF_SERVICE_PERMISSION_UPDATE (1u << 3)
#define OPENREF_SERVICE_PERMISSION_FACTORY_TEST (1u << 4)
#define OPENREF_SERVICE_PERMISSION_IDENTITY (1u << 5)

typedef enum {
    OPENREF_SERVICE_ROLE_FIELD = 1,
    OPENREF_SERVICE_ROLE_TECHNICIAN = 2,
    OPENREF_SERVICE_ROLE_FACTORY = 3
} openref_service_role_t;

typedef bool (*openref_service_verify_fn)(
    void *context,
    const uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES],
    uint32_t counter,
    openref_service_role_t role,
    uint32_t requested_permissions,
    const uint8_t response[OPENREF_SERVICE_RESPONSE_BYTES]);
typedef bool (*openref_service_persist_counter_fn)(
    void *context, uint32_t counter);

typedef struct {
    openref_service_verify_fn verify;
    openref_service_persist_counter_fn persist_counter;
    void *context;
} openref_service_backend_t;

typedef struct {
    uint32_t challenge_timeout_ms;
    uint32_t session_timeout_ms;
    uint32_t lockout_ms;
    uint8_t maximum_failures;
} openref_service_config_t;

typedef struct {
    openref_service_config_t config;
    openref_service_backend_t backend;
    uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES];
    uint64_t challenge_issued_ms;
    uint64_t session_expires_ms;
    uint64_t locked_until_ms;
    uint64_t last_time_ms;
    uint32_t last_counter;
    uint32_t permissions;
    uint32_t successful_sessions;
    uint32_t rejected_attempts;
    uint8_t consecutive_failures;
    bool challenge_active;
    bool session_active;
} openref_service_session_t;

bool openref_service_session_init(
    openref_service_session_t *session,
    const openref_service_config_t *config,
    openref_service_backend_t backend,
    uint32_t persisted_counter,
    uint64_t now_ms);

bool openref_service_issue_challenge(
    openref_service_session_t *session,
    const uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES],
    uint64_t now_ms);

bool openref_service_authorize(
    openref_service_session_t *session,
    uint32_t counter,
    openref_service_role_t role,
    uint32_t requested_permissions,
    bool physical_presence,
    const uint8_t response[OPENREF_SERVICE_RESPONSE_BYTES],
    uint64_t now_ms);

bool openref_service_permitted(
    openref_service_session_t *session,
    uint32_t permission,
    uint64_t now_ms);

void openref_service_end(openref_service_session_t *session);

#endif
