#include "openref_accessory_monitor.h"

#include <stddef.h>
#include <string.h>

static openref_accessory_state_t classify(
    const openref_accessory_monitor_t *monitor,
    bool connector_present,
    bool measurement_valid,
    uint16_t sense_mv)
{
    if (!measurement_valid) {
        return OPENREF_ACCESSORY_SENSOR_FAULT;
    }
    if (!connector_present) {
        return OPENREF_ACCESSORY_DISCONNECTED;
    }
    if (monitor->state == OPENREF_ACCESSORY_MIC_SHORT &&
        sense_mv < monitor->config.short_exit_mv) {
        return OPENREF_ACCESSORY_MIC_SHORT;
    }
    if (monitor->state == OPENREF_ACCESSORY_MIC_OPEN &&
        sense_mv > monitor->config.open_exit_mv) {
        return OPENREF_ACCESSORY_MIC_OPEN;
    }
    if (sense_mv <= monitor->config.short_enter_mv) {
        return OPENREF_ACCESSORY_MIC_SHORT;
    }
    if (sense_mv >= monitor->config.open_enter_mv) {
        return OPENREF_ACCESSORY_MIC_OPEN;
    }
    return OPENREF_ACCESSORY_OK;
}

bool openref_accessory_monitor_init(openref_accessory_monitor_t *monitor,
    const openref_accessory_config_t *config)
{
    if (monitor == NULL || config == NULL || config->confirmation_samples == 0u ||
        !(config->short_enter_mv < config->short_exit_mv &&
          config->short_exit_mv < config->open_exit_mv &&
          config->open_exit_mv < config->open_enter_mv)) {
        return false;
    }
    memset(monitor, 0, sizeof(*monitor));
    monitor->config = *config;
    monitor->state = OPENREF_ACCESSORY_SENSOR_FAULT;
    monitor->candidate = OPENREF_ACCESSORY_SENSOR_FAULT;
    return true;
}

openref_accessory_output_t openref_accessory_monitor_update(
    openref_accessory_monitor_t *monitor, bool connector_present,
    bool measurement_valid, uint16_t microphone_sense_mv)
{
    openref_accessory_output_t output = {
        .state = OPENREF_ACCESSORY_SENSOR_FAULT,
        .mute_transmit = true,
        .mute_playback = true,
    };
    if (monitor == NULL) {
        return output;
    }
    openref_accessory_state_t raw = classify(
        monitor, connector_present, measurement_valid, microphone_sense_mv);
    if (raw != OPENREF_ACCESSORY_OK) {
        monitor->fault_samples++;
    }
    if (raw != monitor->candidate) {
        monitor->candidate = raw;
        monitor->candidate_samples = 1u;
    } else if (monitor->candidate_samples < UINT8_MAX) {
        monitor->candidate_samples++;
    }
    if (monitor->candidate != monitor->state &&
        monitor->candidate_samples >= monitor->config.confirmation_samples) {
        monitor->state = monitor->candidate;
        monitor->transitions++;
        output.state_changed = true;
    }
    output.state = monitor->state;
    output.mute_transmit = raw != OPENREF_ACCESSORY_OK ||
        monitor->state != OPENREF_ACCESSORY_OK;
    output.mute_playback = !connector_present || !measurement_valid;
    return output;
}
