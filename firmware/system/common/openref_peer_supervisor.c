#include "openref_peer_supervisor.h"

#include <stddef.h>

bool openref_peer_supervisor_init(
    openref_peer_supervisor_t *supervisor,
    const openref_peer_config_t *config,
    uint64_t now_ms)
{
    if (supervisor == NULL || config == NULL ||
        config->heartbeat_timeout_ms == 0u || config->reset_hold_ms == 0u ||
        config->boot_wait_ms == 0u || config->power_cycle_wait_ms == 0u ||
        config->maximum_reset_attempts == 0u) {
        return false;
    }
    *supervisor = (openref_peer_supervisor_t){0};
    supervisor->config = *config;
    supervisor->state = OPENREF_PEER_HEALTHY;
    supervisor->last_heartbeat_ms = now_ms;
    supervisor->state_since_ms = now_ms;
    return true;
}

void openref_peer_supervisor_heartbeat(
    openref_peer_supervisor_t *supervisor,
    uint64_t now_ms)
{
    if (supervisor == NULL) {
        return;
    }
    supervisor->heartbeat_count++;
    supervisor->last_heartbeat_ms = now_ms;
    if (supervisor->state != OPENREF_PEER_HEALTHY) {
        supervisor->recovery_count++;
    }
    supervisor->state = OPENREF_PEER_HEALTHY;
    supervisor->state_since_ms = now_ms;
    supervisor->reset_attempts = 0u;
}

uint32_t openref_peer_supervisor_tick(
    openref_peer_supervisor_t *supervisor,
    uint64_t now_ms)
{
    if (supervisor == NULL) {
        return OPENREF_PEER_ACTION_MUTE_AUDIO |
            OPENREF_PEER_ACTION_REPORT_FAULT;
    }
    switch (supervisor->state) {
    case OPENREF_PEER_HEALTHY:
        if (now_ms - supervisor->last_heartbeat_ms <=
            supervisor->config.heartbeat_timeout_ms) {
            return 0u;
        }
        supervisor->timeout_count++;
        supervisor->reset_attempts = 1u;
        supervisor->state = OPENREF_PEER_RESET_ASSERTED;
        supervisor->state_since_ms = now_ms;
        return OPENREF_PEER_ACTION_MUTE_AUDIO |
            OPENREF_PEER_ACTION_ASSERT_RESET |
            OPENREF_PEER_ACTION_REPORT_FAULT;
    case OPENREF_PEER_RESET_ASSERTED:
        if (now_ms - supervisor->state_since_ms <
            supervisor->config.reset_hold_ms) {
            return OPENREF_PEER_ACTION_MUTE_AUDIO;
        }
        supervisor->state = OPENREF_PEER_BOOT_WAIT;
        supervisor->state_since_ms = now_ms;
        return OPENREF_PEER_ACTION_MUTE_AUDIO |
            OPENREF_PEER_ACTION_RELEASE_RESET;
    case OPENREF_PEER_BOOT_WAIT:
        if (now_ms - supervisor->state_since_ms < supervisor->config.boot_wait_ms) {
            return OPENREF_PEER_ACTION_MUTE_AUDIO;
        }
        if (supervisor->reset_attempts < supervisor->config.maximum_reset_attempts) {
            supervisor->reset_attempts++;
            supervisor->state = OPENREF_PEER_RESET_ASSERTED;
            supervisor->state_since_ms = now_ms;
            return OPENREF_PEER_ACTION_MUTE_AUDIO |
                OPENREF_PEER_ACTION_ASSERT_RESET;
        }
        supervisor->power_cycle_count++;
        supervisor->state = OPENREF_PEER_POWER_CYCLE_WAIT;
        supervisor->state_since_ms = now_ms;
        return OPENREF_PEER_ACTION_MUTE_AUDIO |
            OPENREF_PEER_ACTION_POWER_CYCLE |
            OPENREF_PEER_ACTION_REPORT_FAULT;
    case OPENREF_PEER_POWER_CYCLE_WAIT:
        if (now_ms - supervisor->state_since_ms <
            supervisor->config.power_cycle_wait_ms) {
            return OPENREF_PEER_ACTION_MUTE_AUDIO;
        }
        supervisor->state = OPENREF_PEER_FAILED;
        supervisor->state_since_ms = now_ms;
        return OPENREF_PEER_ACTION_MUTE_AUDIO |
            OPENREF_PEER_ACTION_REPORT_FAULT;
    case OPENREF_PEER_FAILED:
    default:
        return OPENREF_PEER_ACTION_MUTE_AUDIO |
            OPENREF_PEER_ACTION_REPORT_FAULT;
    }
}
