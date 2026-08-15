#include <assert.h>

#include "openref_accessory_monitor.h"
#include "openref_power_supervisor.h"
#include "openref_safety_arbiter.h"
#include "openref_startup_supervisor.h"

int main(void)
{
    openref_power_config_t power_config = {
        .low_runtime_minutes = 45u,
        .critical_runtime_minutes = 10u,
        .runtime_hysteresis_minutes = 2u,
        .hard_undervoltage_mv = 3000u,
        .maximum_temperature_cdeg = 6000,
        .critical_grace_ms = 1000u,
    };
    openref_power_supervisor_t power;
    assert(openref_power_supervisor_init(&power, &power_config));
    openref_power_sample_t sample = {
        .pack_present = true, .measurement_valid = true,
        .estimated_runtime_minutes = 120u, .battery_mv = 3800u,
        .temperature_cdeg = 2500, .timestamp_ms = 1u,
    };
    uint32_t power_actions = openref_power_supervisor_update(&power, &sample);

    openref_startup_config_t startup_config = {100u, 200u};
    openref_startup_supervisor_t startup;
    assert(openref_startup_supervisor_init(&startup, &startup_config, 0u));
    openref_startup_inputs_t startup_inputs = {.power_safe = true};
    openref_startup_supervisor_tick(&startup, &startup_inputs, 1u);
    startup_inputs.rails_good = true;
    openref_startup_supervisor_tick(&startup, &startup_inputs, 2u);
    startup_inputs.authenticated_boot = true;
    startup_inputs.configuration_valid = true;
    startup_inputs.accessory_safe = true;
    startup_inputs.peer_healthy = true;
    openref_startup_supervisor_tick(&startup, &startup_inputs, 3u);
    startup_inputs.crew_session_valid = true;
    uint32_t startup_actions =
        openref_startup_supervisor_tick(&startup, &startup_inputs, 4u);

    openref_accessory_config_t accessory_config = {
        200u, 300u, 1700u, 1800u, 3u,
    };
    openref_accessory_monitor_t accessory;
    assert(openref_accessory_monitor_init(&accessory, &accessory_config));
    openref_accessory_output_t accessory_output = {0};
    for (uint8_t i = 0u; i < 3u; i++) {
        accessory_output = openref_accessory_monitor_update(
            &accessory, true, true, 1000u);
    }

    openref_safety_inputs_t safety = {
        .power_actions = power_actions,
        .startup_actions = startup_actions,
        .accessory_mute_transmit = accessory_output.mute_transmit,
        .accessory_mute_playback = accessory_output.mute_playback,
        .watchdog_healthy = true,
    };
    openref_safety_output_t output = openref_safety_arbitrate(&safety);
    assert(output.voice_uplink_enabled && output.playback_enabled &&
           output.network_control_tx_enabled);

    accessory_output = openref_accessory_monitor_update(
        &accessory, false, true, 1000u);
    safety.accessory_mute_transmit = accessory_output.mute_transmit;
    safety.accessory_mute_playback = accessory_output.mute_playback;
    output = openref_safety_arbitrate(&safety);
    assert(!output.voice_uplink_enabled && !output.playback_enabled);
    assert(output.network_control_tx_enabled);

    sample.battery_mv = 2900u;
    sample.timestamp_ms = 2u;
    safety.power_actions = openref_power_supervisor_update(&power, &sample);
    output = openref_safety_arbitrate(&safety);
    assert(!output.voice_uplink_enabled && !output.playback_enabled &&
           !output.network_control_tx_enabled);
    assert((output.radio_inhibit_reasons & OPENREF_INHIBIT_POWER) != 0u);
    return 0;
}
