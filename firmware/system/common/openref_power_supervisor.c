#include "openref_power_supervisor.h"

#include <stddef.h>

static void set_state(
    openref_power_supervisor_t *supervisor,
    openref_power_state_t state)
{
    if (supervisor->state != state) {
        supervisor->state = state;
        supervisor->transitions++;
    }
}

bool openref_power_supervisor_init(
    openref_power_supervisor_t *supervisor,
    const openref_power_config_t *config)
{
    if (supervisor == NULL || config == NULL ||
        config->critical_runtime_minutes == 0u ||
        config->low_runtime_minutes <= config->critical_runtime_minutes ||
        config->runtime_hysteresis_minutes == 0u ||
        config->low_runtime_minutes >
            UINT16_MAX - config->runtime_hysteresis_minutes ||
        config->critical_runtime_minutes >
            UINT16_MAX - config->runtime_hysteresis_minutes ||
        config->hard_undervoltage_mv == 0u ||
        config->maximum_temperature_cdeg <= 0 ||
        config->critical_grace_ms == 0u) {
        return false;
    }
    *supervisor = (openref_power_supervisor_t){0};
    supervisor->config = *config;
    supervisor->state = OPENREF_POWER_DISCONNECTED;
    return true;
}

uint32_t openref_power_supervisor_update(
    openref_power_supervisor_t *supervisor,
    const openref_power_sample_t *sample)
{
    if (supervisor == NULL || sample == NULL) {
        return OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    }
    supervisor->samples++;
    if (!sample->pack_present) {
        supervisor->shutdown_latched = false;
        supervisor->critical_timer_active = false;
        set_state(supervisor, OPENREF_POWER_DISCONNECTED);
        return OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    }
    if (supervisor->shutdown_latched) {
        set_state(supervisor, OPENREF_POWER_SHUTDOWN);
        return OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    }
    if (!sample->measurement_valid) {
        supervisor->invalid_samples++;
        supervisor->shutdown_latched = true;
        set_state(supervisor, OPENREF_POWER_SENSOR_FAULT);
        return OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    }
    if (sample->temperature_cdeg >= supervisor->config.maximum_temperature_cdeg) {
        supervisor->overtemperature_events++;
        supervisor->shutdown_latched = true;
        set_state(supervisor, OPENREF_POWER_OVERTEMPERATURE);
        return OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    }
    if (sample->battery_mv <= supervisor->config.hard_undervoltage_mv) {
        supervisor->undervoltage_events++;
        supervisor->shutdown_latched = true;
        set_state(supervisor, OPENREF_POWER_SHUTDOWN);
        return OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    }

    uint16_t critical_exit = (uint16_t)(
        supervisor->config.critical_runtime_minutes +
        supervisor->config.runtime_hysteresis_minutes);
    bool critical = sample->estimated_runtime_minutes <=
        supervisor->config.critical_runtime_minutes ||
        (supervisor->state == OPENREF_POWER_CRITICAL &&
         sample->estimated_runtime_minutes < critical_exit);
    if (critical) {
        if (!supervisor->critical_timer_active) {
            supervisor->critical_since_ms = sample->timestamp_ms;
            supervisor->critical_timer_active = true;
        }
        set_state(supervisor, OPENREF_POWER_CRITICAL);
        if (sample->timestamp_ms - supervisor->critical_since_ms >=
            supervisor->config.critical_grace_ms) {
            supervisor->shutdown_latched = true;
            set_state(supervisor, OPENREF_POWER_SHUTDOWN);
            return OPENREF_POWER_ACTION_WARN_CRITICAL |
                OPENREF_POWER_ACTION_MUTE_AUDIO |
                OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
        }
        return OPENREF_POWER_ACTION_WARN_CRITICAL |
            OPENREF_POWER_ACTION_REDUCE_LOAD;
    }
    supervisor->critical_timer_active = false;

    uint16_t low_exit = (uint16_t)(
        supervisor->config.low_runtime_minutes +
        supervisor->config.runtime_hysteresis_minutes);
    bool low = sample->estimated_runtime_minutes <=
        supervisor->config.low_runtime_minutes ||
        (supervisor->state == OPENREF_POWER_LOW &&
         sample->estimated_runtime_minutes < low_exit);
    if (low) {
        set_state(supervisor, OPENREF_POWER_LOW);
        return OPENREF_POWER_ACTION_WARN_LOW;
    }
    set_state(supervisor, OPENREF_POWER_NORMAL);
    return 0u;
}
