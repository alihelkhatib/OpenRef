#ifndef OPENREF_POWER_SUPERVISOR_H
#define OPENREF_POWER_SUPERVISOR_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_POWER_DISCONNECTED = 0,
    OPENREF_POWER_NORMAL = 1,
    OPENREF_POWER_LOW = 2,
    OPENREF_POWER_CRITICAL = 3,
    OPENREF_POWER_SHUTDOWN = 4,
    OPENREF_POWER_OVERTEMPERATURE = 5,
    OPENREF_POWER_SENSOR_FAULT = 6
} openref_power_state_t;

#define OPENREF_POWER_ACTION_WARN_LOW (1u << 0)
#define OPENREF_POWER_ACTION_WARN_CRITICAL (1u << 1)
#define OPENREF_POWER_ACTION_REDUCE_LOAD (1u << 2)
#define OPENREF_POWER_ACTION_MUTE_AUDIO (1u << 3)
#define OPENREF_POWER_ACTION_REQUEST_SHUTDOWN (1u << 4)

typedef struct {
    uint16_t low_runtime_minutes;
    uint16_t critical_runtime_minutes;
    uint16_t runtime_hysteresis_minutes;
    uint16_t hard_undervoltage_mv;
    int16_t maximum_temperature_cdeg;
    uint32_t critical_grace_ms;
} openref_power_config_t;

typedef struct {
    bool pack_present;
    bool measurement_valid;
    uint16_t estimated_runtime_minutes;
    uint16_t battery_mv;
    int16_t temperature_cdeg;
    uint64_t timestamp_ms;
} openref_power_sample_t;

typedef struct {
    openref_power_config_t config;
    openref_power_state_t state;
    uint64_t critical_since_ms;
    bool critical_timer_active;
    bool shutdown_latched;
    uint32_t samples;
    uint32_t transitions;
    uint32_t invalid_samples;
    uint32_t undervoltage_events;
    uint32_t overtemperature_events;
} openref_power_supervisor_t;

bool openref_power_supervisor_init(
    openref_power_supervisor_t *supervisor,
    const openref_power_config_t *config);

uint32_t openref_power_supervisor_update(
    openref_power_supervisor_t *supervisor,
    const openref_power_sample_t *sample);

#endif
