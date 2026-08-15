#include "openref_startup_supervisor.h"

#include <stddef.h>
#include <string.h>

static void transition(openref_startup_supervisor_t *s,
                       openref_startup_state_t state, uint64_t now_ms)
{
    if (s->state != state) {
        s->state = state;
        s->state_since_ms = now_ms;
        s->transition_count++;
    }
}

static uint32_t actions(const openref_startup_supervisor_t *s)
{
    switch (s->state) {
    case OPENREF_STARTUP_POWER_WAIT:
        return OPENREF_STARTUP_ACTION_ENABLE_RAILS |
            OPENREF_STARTUP_ACTION_MUTE_AUDIO;
    case OPENREF_STARTUP_PROCESSOR_WAIT:
        return OPENREF_STARTUP_ACTION_ENABLE_RAILS |
            OPENREF_STARTUP_ACTION_RELEASE_RESETS |
            OPENREF_STARTUP_ACTION_MUTE_AUDIO;
    case OPENREF_STARTUP_LOCAL_READY:
        return OPENREF_STARTUP_ACTION_ENABLE_RAILS |
            OPENREF_STARTUP_ACTION_RELEASE_RESETS |
            OPENREF_STARTUP_ACTION_MUTE_AUDIO |
            OPENREF_STARTUP_ACTION_REPORT_READY;
    case OPENREF_STARTUP_OPERATIONAL:
        return OPENREF_STARTUP_ACTION_ENABLE_RAILS |
            OPENREF_STARTUP_ACTION_RELEASE_RESETS |
            OPENREF_STARTUP_ACTION_PERMIT_RF_TX |
            OPENREF_STARTUP_ACTION_REPORT_READY;
    case OPENREF_STARTUP_FAULT:
        return OPENREF_STARTUP_ACTION_MUTE_AUDIO |
            OPENREF_STARTUP_ACTION_REPORT_FAULT;
    default:
        return OPENREF_STARTUP_ACTION_MUTE_AUDIO;
    }
}

bool openref_startup_supervisor_init(openref_startup_supervisor_t *s,
    const openref_startup_config_t *config, uint64_t now_ms)
{
    if (s == NULL || config == NULL || config->rail_timeout_ms == 0u ||
        config->processor_timeout_ms == 0u) {
        return false;
    }
    memset(s, 0, sizeof(*s));
    s->config = *config;
    s->state = OPENREF_STARTUP_SAFE;
    s->state_since_ms = now_ms;
    s->last_tick_ms = now_ms;
    return true;
}

uint32_t openref_startup_supervisor_tick(openref_startup_supervisor_t *s,
    const openref_startup_inputs_t *in, uint64_t now_ms)
{
    if (s == NULL || in == NULL) {
        return OPENREF_STARTUP_ACTION_MUTE_AUDIO |
            OPENREF_STARTUP_ACTION_REPORT_FAULT;
    }
    if (now_ms < s->last_tick_ms) {
        s->fault_mask |= OPENREF_STARTUP_FAULT_CLOCK;
        transition(s, OPENREF_STARTUP_FAULT, now_ms);
        return actions(s);
    }
    s->last_tick_ms = now_ms;
    if (!in->power_safe) {
        s->fault_mask = 0u;
        transition(s, OPENREF_STARTUP_SAFE, now_ms);
        return actions(s);
    }
    switch (s->state) {
    case OPENREF_STARTUP_SAFE:
        transition(s, OPENREF_STARTUP_POWER_WAIT, now_ms);
        break;
    case OPENREF_STARTUP_POWER_WAIT:
        if (in->rails_good) {
            transition(s, OPENREF_STARTUP_PROCESSOR_WAIT, now_ms);
        } else if (now_ms - s->state_since_ms > s->config.rail_timeout_ms) {
            s->fault_mask |= OPENREF_STARTUP_FAULT_RAIL_TIMEOUT;
            transition(s, OPENREF_STARTUP_FAULT, now_ms);
        }
        break;
    case OPENREF_STARTUP_PROCESSOR_WAIT:
        if (!in->rails_good) {
            s->fault_mask |= OPENREF_STARTUP_FAULT_RUNTIME_INTERLOCK;
            transition(s, OPENREF_STARTUP_FAULT, now_ms);
        } else if (in->authenticated_boot && in->configuration_valid &&
                   in->accessory_safe && in->peer_healthy) {
            transition(s, OPENREF_STARTUP_LOCAL_READY, now_ms);
        } else if (now_ms - s->state_since_ms > s->config.processor_timeout_ms) {
            s->fault_mask |= OPENREF_STARTUP_FAULT_PROCESSOR_TIMEOUT;
            transition(s, OPENREF_STARTUP_FAULT, now_ms);
        }
        break;
    case OPENREF_STARTUP_LOCAL_READY:
    case OPENREF_STARTUP_OPERATIONAL:
        if (!in->rails_good || !in->authenticated_boot ||
            !in->configuration_valid || !in->accessory_safe ||
            !in->peer_healthy) {
            s->fault_mask |= OPENREF_STARTUP_FAULT_RUNTIME_INTERLOCK;
            transition(s, OPENREF_STARTUP_FAULT, now_ms);
        } else if (in->crew_session_valid) {
            transition(s, OPENREF_STARTUP_OPERATIONAL, now_ms);
        } else {
            transition(s, OPENREF_STARTUP_LOCAL_READY, now_ms);
        }
        break;
    default:
        break;
    }
    return actions(s);
}
