#include "openref_service_session.h"

#include <stddef.h>
#include <string.h>

#define ALL_PERMISSIONS ((1u << 6) - 1u)
#define PHYSICAL_PERMISSIONS (OPENREF_SERVICE_PERMISSION_CONFIG_WRITE | \
    OPENREF_SERVICE_PERMISSION_FACTORY_TEST | OPENREF_SERVICE_PERMISSION_IDENTITY)

static uint64_t deadline(uint64_t now_ms, uint32_t duration_ms)
{
    return UINT64_MAX - now_ms < duration_ms
        ? UINT64_MAX
        : now_ms + duration_ms;
}

static uint32_t role_permissions(openref_service_role_t role)
{
    switch (role) {
    case OPENREF_SERVICE_ROLE_FIELD:
        return OPENREF_SERVICE_PERMISSION_DIAGNOSTICS |
            OPENREF_SERVICE_PERMISSION_CONFIG_READ |
            OPENREF_SERVICE_PERMISSION_UPDATE;
    case OPENREF_SERVICE_ROLE_TECHNICIAN:
        return OPENREF_SERVICE_PERMISSION_DIAGNOSTICS |
            OPENREF_SERVICE_PERMISSION_CONFIG_READ |
            OPENREF_SERVICE_PERMISSION_CONFIG_WRITE |
            OPENREF_SERVICE_PERMISSION_UPDATE;
    case OPENREF_SERVICE_ROLE_FACTORY:
        return ALL_PERMISSIONS;
    default:
        return 0u;
    }
}

void openref_service_end(openref_service_session_t *session)
{
    if (session == NULL) {
        return;
    }
    memset(session->challenge, 0, sizeof(session->challenge));
    session->challenge_active = false;
    session->session_active = false;
    session->permissions = 0u;
    session->session_expires_ms = 0u;
}

static bool time_valid(openref_service_session_t *session, uint64_t now_ms)
{
    if (now_ms < session->last_time_ms) {
        openref_service_end(session);
        session->rejected_attempts++;
        return false;
    }
    session->last_time_ms = now_ms;
    return true;
}

static bool reject(openref_service_session_t *session, uint64_t now_ms)
{
    session->rejected_attempts++;
    if (session->consecutive_failures < UINT8_MAX) {
        session->consecutive_failures++;
    }
    session->challenge_active = false;
    memset(session->challenge, 0, sizeof(session->challenge));
    if (session->consecutive_failures >= session->config.maximum_failures) {
        session->locked_until_ms = deadline(now_ms, session->config.lockout_ms);
    }
    return false;
}

bool openref_service_session_init(openref_service_session_t *session,
    const openref_service_config_t *config, openref_service_backend_t backend,
    uint32_t persisted_counter, uint64_t now_ms)
{
    if (session == NULL || config == NULL || config->challenge_timeout_ms == 0u ||
        config->session_timeout_ms == 0u || config->lockout_ms == 0u ||
        config->maximum_failures == 0u || backend.verify == NULL ||
        backend.persist_counter == NULL) {
        return false;
    }
    memset(session, 0, sizeof(*session));
    session->config = *config;
    session->backend = backend;
    session->last_counter = persisted_counter;
    session->last_time_ms = now_ms;
    return true;
}

bool openref_service_issue_challenge(openref_service_session_t *session,
    const uint8_t challenge[OPENREF_SERVICE_CHALLENGE_BYTES], uint64_t now_ms)
{
    if (session == NULL || challenge == NULL || !time_valid(session, now_ms) ||
        now_ms < session->locked_until_ms) {
        return false;
    }
    uint8_t aggregate = 0u;
    for (uint8_t i = 0u; i < OPENREF_SERVICE_CHALLENGE_BYTES; i++) {
        aggregate |= challenge[i];
    }
    if (aggregate == 0u) {
        return reject(session, now_ms);
    }
    openref_service_end(session);
    memcpy(session->challenge, challenge, sizeof(session->challenge));
    session->challenge_issued_ms = now_ms;
    session->challenge_active = true;
    return true;
}

bool openref_service_authorize(openref_service_session_t *session,
    uint32_t counter, openref_service_role_t role,
    uint32_t requested_permissions, bool physical_presence,
    const uint8_t response[OPENREF_SERVICE_RESPONSE_BYTES], uint64_t now_ms)
{
    if (session == NULL || response == NULL || !time_valid(session, now_ms) ||
        now_ms < session->locked_until_ms) {
        return false;
    }
    uint32_t allowed = role_permissions(role);
    bool valid = session->challenge_active &&
        now_ms - session->challenge_issued_ms <=
            session->config.challenge_timeout_ms &&
        counter > session->last_counter && requested_permissions != 0u &&
        (requested_permissions & ~ALL_PERMISSIONS) == 0u &&
        (requested_permissions & ~allowed) == 0u &&
        (physical_presence ||
         (requested_permissions & PHYSICAL_PERMISSIONS) == 0u) &&
        session->backend.verify(session->backend.context, session->challenge,
            counter, role, requested_permissions, response);
    if (!valid ||
        !session->backend.persist_counter(session->backend.context, counter)) {
        return reject(session, now_ms);
    }
    memset(session->challenge, 0, sizeof(session->challenge));
    session->challenge_active = false;
    session->last_counter = counter;
    session->permissions = requested_permissions;
    session->session_expires_ms = deadline(
        now_ms, session->config.session_timeout_ms);
    session->session_active = true;
    session->consecutive_failures = 0u;
    session->successful_sessions++;
    return true;
}

bool openref_service_permitted(openref_service_session_t *session,
    uint32_t permission, uint64_t now_ms)
{
    if (session == NULL || !time_valid(session, now_ms) ||
        !session->session_active || now_ms > session->session_expires_ms ||
        permission == 0u || (permission & (permission - 1u)) != 0u ||
        (session->permissions & permission) == 0u) {
        if (session != NULL && session->session_active &&
            now_ms > session->session_expires_ms) {
            openref_service_end(session);
        }
        return false;
    }
    return true;
}
