#ifndef OPENREF_ACCESSORY_MONITOR_H
#define OPENREF_ACCESSORY_MONITOR_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_ACCESSORY_OK = 0,
    OPENREF_ACCESSORY_DISCONNECTED,
    OPENREF_ACCESSORY_MIC_SHORT,
    OPENREF_ACCESSORY_MIC_OPEN,
    OPENREF_ACCESSORY_SENSOR_FAULT
} openref_accessory_state_t;

typedef struct {
    uint16_t short_enter_mv;
    uint16_t short_exit_mv;
    uint16_t open_exit_mv;
    uint16_t open_enter_mv;
    uint8_t confirmation_samples;
} openref_accessory_config_t;

typedef struct {
    openref_accessory_state_t state;
    bool mute_transmit;
    bool mute_playback;
    bool state_changed;
} openref_accessory_output_t;

typedef struct {
    openref_accessory_config_t config;
    openref_accessory_state_t state;
    openref_accessory_state_t candidate;
    uint8_t candidate_samples;
    uint32_t transitions;
    uint32_t fault_samples;
} openref_accessory_monitor_t;

bool openref_accessory_monitor_init(
    openref_accessory_monitor_t *monitor,
    const openref_accessory_config_t *config);

openref_accessory_output_t openref_accessory_monitor_update(
    openref_accessory_monitor_t *monitor,
    bool connector_present,
    bool measurement_valid,
    uint16_t microphone_sense_mv);

#endif
