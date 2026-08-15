#ifndef OPENREF_CHARGE_SUPERVISOR_H
#define OPENREF_CHARGE_SUPERVISOR_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_CHARGE_EMPTY = 0,
    OPENREF_CHARGE_PRECHECK,
    OPENREF_CHARGE_ACTIVE,
    OPENREF_CHARGE_COMPLETE,
    OPENREF_CHARGE_FAULT
} openref_charge_state_t;

#define OPENREF_CHARGE_FAULT_PACK_ID (1u << 0)
#define OPENREF_CHARGE_FAULT_SENSOR (1u << 1)
#define OPENREF_CHARGE_FAULT_TEMPERATURE (1u << 2)
#define OPENREF_CHARGE_FAULT_VOLTAGE (1u << 3)
#define OPENREF_CHARGE_FAULT_CHARGER (1u << 4)
#define OPENREF_CHARGE_FAULT_TIMEOUT (1u << 5)
#define OPENREF_CHARGE_FAULT_CLOCK (1u << 6)

typedef struct {
    int16_t minimum_temperature_deci_c;
    int16_t maximum_temperature_deci_c;
    uint16_t minimum_pack_mv;
    uint16_t maximum_pack_mv;
    uint32_t maximum_charge_ms;
} openref_charge_config_t;

typedef struct {
    bool pack_present;
    bool pack_identity_valid;
    bool sensors_valid;
    int16_t temperature_deci_c;
    uint16_t pack_mv;
    bool charger_fault;
    bool charge_complete;
} openref_charge_inputs_t;

typedef struct {
    openref_charge_config_t config;
    openref_charge_state_t state;
    uint64_t state_since_ms;
    uint64_t last_tick_ms;
    uint32_t fault_mask;
    uint32_t completed_charges;
    uint32_t fault_count;
    bool charge_enable;
} openref_charge_supervisor_t;

bool openref_charge_supervisor_init(
    openref_charge_supervisor_t *supervisor,
    const openref_charge_config_t *config,
    uint64_t now_ms);

openref_charge_state_t openref_charge_supervisor_tick(
    openref_charge_supervisor_t *supervisor,
    const openref_charge_inputs_t *inputs,
    uint64_t now_ms);

#endif
