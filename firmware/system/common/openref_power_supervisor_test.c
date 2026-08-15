#include <assert.h>
#include <stdint.h>

#include "openref_power_supervisor.h"

static const openref_power_config_t CONFIG = {
    .low_runtime_minutes = 45u,
    .critical_runtime_minutes = 10u,
    .runtime_hysteresis_minutes = 5u,
    .hard_undervoltage_mv = 3000u,
    .maximum_temperature_cdeg = 6000,
    .critical_grace_ms = 600000u,
};

static openref_power_sample_t sample(uint16_t minutes, uint64_t timestamp_ms)
{
    return (openref_power_sample_t){
        .pack_present = true,
        .measurement_valid = true,
        .estimated_runtime_minutes = minutes,
        .battery_mv = 3700u,
        .temperature_cdeg = 2500,
        .timestamp_ms = timestamp_ms,
    };
}

int main(void)
{
    openref_power_supervisor_t supervisor;
    assert(openref_power_supervisor_init(&supervisor, &CONFIG));
    openref_power_config_t invalid = CONFIG;
    invalid.low_runtime_minutes = UINT16_MAX;
    assert(!openref_power_supervisor_init(&supervisor, &invalid));
    assert(openref_power_supervisor_init(&supervisor, &CONFIG));
    openref_power_sample_t input = sample(100u, 0u);
    assert(openref_power_supervisor_update(&supervisor, &input) == 0u);
    assert(supervisor.state == OPENREF_POWER_NORMAL);

    input = sample(45u, 1000u);
    assert(openref_power_supervisor_update(&supervisor, &input) ==
           OPENREF_POWER_ACTION_WARN_LOW);
    input = sample(48u, 2000u);
    assert(openref_power_supervisor_update(&supervisor, &input) ==
           OPENREF_POWER_ACTION_WARN_LOW);
    input = sample(51u, 3000u);
    assert(openref_power_supervisor_update(&supervisor, &input) == 0u);

    input = sample(10u, 10000u);
    assert(openref_power_supervisor_update(&supervisor, &input) ==
           (OPENREF_POWER_ACTION_WARN_CRITICAL |
            OPENREF_POWER_ACTION_REDUCE_LOAD));
    input = sample(10u, 609999u);
    assert((openref_power_supervisor_update(&supervisor, &input) &
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN) == 0u);
    input = sample(10u, 610000u);
    assert(openref_power_supervisor_update(&supervisor, &input) ==
           (OPENREF_POWER_ACTION_WARN_CRITICAL |
            OPENREF_POWER_ACTION_MUTE_AUDIO |
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN));
    assert(supervisor.shutdown_latched);

    input = sample(100u, 620000u);
    assert((openref_power_supervisor_update(&supervisor, &input) &
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN) != 0u);
    input.pack_present = false;
    (void)openref_power_supervisor_update(&supervisor, &input);
    input = sample(100u, 630000u);
    assert(openref_power_supervisor_update(&supervisor, &input) == 0u);

    input = sample(100u, 640000u);
    input.temperature_cdeg = 6000;
    assert((openref_power_supervisor_update(&supervisor, &input) &
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN) != 0u);
    assert(supervisor.overtemperature_events == 1u);

    input.pack_present = false;
    (void)openref_power_supervisor_update(&supervisor, &input);
    input = sample(100u, 650000u);
    input.battery_mv = 3000u;
    assert((openref_power_supervisor_update(&supervisor, &input) &
            OPENREF_POWER_ACTION_REQUEST_SHUTDOWN) != 0u);
    assert(supervisor.undervoltage_events == 1u);
    return 0;
}
