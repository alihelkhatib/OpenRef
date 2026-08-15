#include "openref_status_policy.h"

#include <stddef.h>
#include <string.h>

void openref_status_policy_init(openref_status_policy_t *policy)
{
    if (policy != NULL) {
        memset(policy, 0, sizeof(*policy));
    }
}

openref_status_output_t openref_status_policy_update(
    openref_status_policy_t *policy,
    const openref_status_inputs_t *in)
{
    openref_status_output_t out = {.mode = OPENREF_STATUS_FAULT};
    if (policy == NULL || in == NULL) {
        return out;
    }
    bool inconsistent = (in->forming && in->connected) ||
        (in->battery_critical && !in->battery_low) ||
        (!in->powered && (in->forming || in->connected || in->update_recovery));
    if (inconsistent) {
        policy->inconsistent_input_count++;
    }

    if (in->battery_low) {
        out.alerts |= OPENREF_STATUS_ALERT_LOW_BATTERY;
    }
    if (in->battery_critical) {
        out.alerts |= OPENREF_STATUS_ALERT_CRITICAL_BATTERY;
    }
    if (in->link_degraded) {
        out.alerts |= OPENREF_STATUS_ALERT_DEGRADED_LINK;
    }
    if (!in->accessory_safe && in->powered) {
        out.alerts |= OPENREF_STATUS_ALERT_ACCESSORY;
    }

    bool effective_fault = in->fault || inconsistent;
    if (effective_fault) {
        out.mode = OPENREF_STATUS_FAULT;
    } else if (!in->powered && !in->charging) {
        out.mode = OPENREF_STATUS_OFF;
    } else if (in->update_recovery) {
        out.mode = OPENREF_STATUS_UPDATE_RECOVERY;
    } else if (in->charging && !in->connected && !in->forming) {
        out.mode = OPENREF_STATUS_CHARGING;
    } else if (in->forming) {
        out.mode = OPENREF_STATUS_FORMING;
    } else if (in->connected) {
        out.mode = OPENREF_STATUS_CONNECTED;
    } else {
        out.mode = OPENREF_STATUS_BOOTING;
    }
    out.operational_ready = out.mode == OPENREF_STATUS_CONNECTED &&
        (out.alerts & (OPENREF_STATUS_ALERT_CRITICAL_BATTERY |
                       OPENREF_STATUS_ALERT_DEGRADED_LINK |
                       OPENREF_STATUS_ALERT_ACCESSORY)) == 0u;

    uint8_t rising = (uint8_t)(out.alerts & (uint8_t)~policy->previous_alerts);
    if ((rising & OPENREF_STATUS_ALERT_CRITICAL_BATTERY) != 0u) {
        out.attention_events |= OPENREF_STATUS_ATTENTION_CRITICAL_BATTERY;
    }
    if ((rising & OPENREF_STATUS_ALERT_DEGRADED_LINK) != 0u) {
        out.attention_events |= OPENREF_STATUS_ATTENTION_DEGRADED_LINK;
    }
    if (effective_fault && !policy->previous_fault) {
        out.attention_events |= OPENREF_STATUS_ATTENTION_FAULT;
    }
    policy->previous_alerts = out.alerts;
    policy->previous_fault = effective_fault;
    policy->output = out;
    policy->update_count++;
    return out;
}
