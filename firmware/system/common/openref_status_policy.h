#ifndef OPENREF_STATUS_POLICY_H
#define OPENREF_STATUS_POLICY_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_STATUS_OFF = 0,
    OPENREF_STATUS_BOOTING,
    OPENREF_STATUS_FORMING,
    OPENREF_STATUS_CONNECTED,
    OPENREF_STATUS_CHARGING,
    OPENREF_STATUS_UPDATE_RECOVERY,
    OPENREF_STATUS_FAULT
} openref_status_mode_t;

#define OPENREF_STATUS_ALERT_LOW_BATTERY (1u << 0)
#define OPENREF_STATUS_ALERT_CRITICAL_BATTERY (1u << 1)
#define OPENREF_STATUS_ALERT_DEGRADED_LINK (1u << 2)
#define OPENREF_STATUS_ALERT_ACCESSORY (1u << 3)

#define OPENREF_STATUS_ATTENTION_CRITICAL_BATTERY (1u << 0)
#define OPENREF_STATUS_ATTENTION_DEGRADED_LINK (1u << 1)
#define OPENREF_STATUS_ATTENTION_FAULT (1u << 2)

typedef struct {
    bool powered;
    bool forming;
    bool connected;
    bool charging;
    bool update_recovery;
    bool fault;
    bool battery_low;
    bool battery_critical;
    bool link_degraded;
    bool accessory_safe;
} openref_status_inputs_t;

typedef struct {
    openref_status_mode_t mode;
    uint8_t alerts;
    uint8_t attention_events;
    bool operational_ready;
} openref_status_output_t;

typedef struct {
    openref_status_output_t output;
    uint8_t previous_alerts;
    bool previous_fault;
    uint32_t update_count;
    uint32_t inconsistent_input_count;
} openref_status_policy_t;

void openref_status_policy_init(openref_status_policy_t *policy);

openref_status_output_t openref_status_policy_update(
    openref_status_policy_t *policy,
    const openref_status_inputs_t *inputs);

#endif
