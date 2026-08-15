#include "openref_safety_arbiter.h"

#include <stddef.h>

#include "openref_peer_supervisor.h"
#include "openref_power_supervisor.h"
#include "openref_startup_supervisor.h"

openref_safety_output_t openref_safety_arbitrate(
    const openref_safety_inputs_t *in)
{
    openref_safety_output_t out = {
        .transmit_mute_reasons = OPENREF_INHIBIT_SYSTEM_FAULT,
        .playback_mute_reasons = OPENREF_INHIBIT_SYSTEM_FAULT,
        .radio_inhibit_reasons = OPENREF_INHIBIT_SYSTEM_FAULT,
    };
    if (in == NULL) {
        return out;
    }
    out = (openref_safety_output_t){0};
    if ((in->power_actions & (OPENREF_POWER_ACTION_MUTE_AUDIO |
                              OPENREF_POWER_ACTION_REQUEST_SHUTDOWN)) != 0u) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_POWER;
        out.playback_mute_reasons |= OPENREF_INHIBIT_POWER;
        out.radio_inhibit_reasons |= OPENREF_INHIBIT_POWER;
    }
    if ((in->startup_actions & OPENREF_STARTUP_ACTION_MUTE_AUDIO) != 0u) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_STARTUP;
        out.playback_mute_reasons |= OPENREF_INHIBIT_STARTUP;
    }
    if ((in->startup_actions & OPENREF_STARTUP_ACTION_PERMIT_RF_TX) == 0u) {
        out.radio_inhibit_reasons |= OPENREF_INHIBIT_STARTUP;
    }
    if (in->accessory_mute_transmit) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_ACCESSORY;
    }
    if (in->accessory_mute_playback) {
        out.playback_mute_reasons |= OPENREF_INHIBIT_ACCESSORY;
    }
    if ((in->peer_actions & OPENREF_PEER_ACTION_MUTE_AUDIO) != 0u) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_PEER;
        out.playback_mute_reasons |= OPENREF_INHIBIT_PEER;
    }
    if (!in->watchdog_healthy) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_WATCHDOG;
        out.playback_mute_reasons |= OPENREF_INHIBIT_WATCHDOG;
        out.radio_inhibit_reasons |= OPENREF_INHIBIT_WATCHDOG;
    }
    if (in->update_active) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_UPDATE;
        out.playback_mute_reasons |= OPENREF_INHIBIT_UPDATE;
        out.radio_inhibit_reasons |= OPENREF_INHIBIT_UPDATE;
    }
    if (in->privileged_service_active) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_SERVICE;
        out.playback_mute_reasons |= OPENREF_INHIBIT_SERVICE;
        out.radio_inhibit_reasons |= OPENREF_INHIBIT_SERVICE;
    }
    if (in->user_transmit_mute) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_USER;
    }
    if (in->user_playback_mute) {
        out.playback_mute_reasons |= OPENREF_INHIBIT_USER;
    }
    if (in->system_fault) {
        out.transmit_mute_reasons |= OPENREF_INHIBIT_SYSTEM_FAULT;
        out.playback_mute_reasons |= OPENREF_INHIBIT_SYSTEM_FAULT;
        out.radio_inhibit_reasons |= OPENREF_INHIBIT_SYSTEM_FAULT;
    }
    out.network_control_tx_enabled = out.radio_inhibit_reasons == 0u;
    out.voice_uplink_enabled = out.transmit_mute_reasons == 0u &&
        out.network_control_tx_enabled;
    out.playback_enabled = out.playback_mute_reasons == 0u;
    return out;
}
