#include "openref_charge_supervisor.h"

#include <stddef.h>
#include <string.h>

static void set_state(openref_charge_supervisor_t *s,
                      openref_charge_state_t state, uint64_t now_ms)
{
    if (s->state != state) {
        s->state = state;
        s->state_since_ms = now_ms;
    }
}

static void fault(openref_charge_supervisor_t *s, uint32_t mask,
                  uint64_t now_ms)
{
    if (s->state != OPENREF_CHARGE_FAULT) {
        s->fault_count++;
    }
    s->fault_mask |= mask;
    s->charge_enable = false;
    set_state(s, OPENREF_CHARGE_FAULT, now_ms);
}

bool openref_charge_supervisor_init(openref_charge_supervisor_t *s,
    const openref_charge_config_t *config, uint64_t now_ms)
{
    if (s == NULL || config == NULL ||
        config->minimum_temperature_deci_c >=
            config->maximum_temperature_deci_c ||
        config->minimum_pack_mv >= config->maximum_pack_mv ||
        config->maximum_charge_ms == 0u) {
        return false;
    }
    memset(s, 0, sizeof(*s));
    s->config = *config;
    s->state = OPENREF_CHARGE_EMPTY;
    s->state_since_ms = now_ms;
    s->last_tick_ms = now_ms;
    return true;
}

openref_charge_state_t openref_charge_supervisor_tick(
    openref_charge_supervisor_t *s, const openref_charge_inputs_t *in,
    uint64_t now_ms)
{
    if (s == NULL || in == NULL) {
        return OPENREF_CHARGE_FAULT;
    }
    s->charge_enable = false;
    if (now_ms < s->last_tick_ms) {
        fault(s, OPENREF_CHARGE_FAULT_CLOCK, now_ms);
        return s->state;
    }
    s->last_tick_ms = now_ms;
    if (!in->pack_present) {
        s->fault_mask = 0u;
        set_state(s, OPENREF_CHARGE_EMPTY, now_ms);
        return s->state;
    }
    if (s->state == OPENREF_CHARGE_FAULT) {
        return s->state;
    }
    if (!in->pack_identity_valid) {
        fault(s, OPENREF_CHARGE_FAULT_PACK_ID, now_ms);
    } else if (!in->sensors_valid) {
        fault(s, OPENREF_CHARGE_FAULT_SENSOR, now_ms);
    } else if (in->temperature_deci_c < s->config.minimum_temperature_deci_c ||
               in->temperature_deci_c > s->config.maximum_temperature_deci_c) {
        fault(s, OPENREF_CHARGE_FAULT_TEMPERATURE, now_ms);
    } else if (in->pack_mv < s->config.minimum_pack_mv ||
               in->pack_mv > s->config.maximum_pack_mv) {
        fault(s, OPENREF_CHARGE_FAULT_VOLTAGE, now_ms);
    } else if (in->charger_fault) {
        fault(s, OPENREF_CHARGE_FAULT_CHARGER, now_ms);
    } else if (s->state == OPENREF_CHARGE_ACTIVE &&
               now_ms - s->state_since_ms > s->config.maximum_charge_ms) {
        fault(s, OPENREF_CHARGE_FAULT_TIMEOUT, now_ms);
    } else if (in->charge_complete) {
        if (s->state == OPENREF_CHARGE_ACTIVE) {
            s->completed_charges++;
        }
        set_state(s, OPENREF_CHARGE_COMPLETE, now_ms);
    } else {
        if (s->state == OPENREF_CHARGE_EMPTY) {
            set_state(s, OPENREF_CHARGE_PRECHECK, now_ms);
        } else {
            set_state(s, OPENREF_CHARGE_ACTIVE, now_ms);
            s->charge_enable = true;
        }
    }
    return s->state;
}
