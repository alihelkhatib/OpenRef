#include <assert.h>
#include <string.h>

#include "openref_settings_runtime.h"
#include "openref_system_runtime.h"

typedef struct {
    uint8_t slots[2][OPENREF_CONFIG_SLOT_BYTES];
    bool present[2];
    openref_volume_manager_t *volume;
    bool voice;
    bool network;
} fixture_t;

static bool read_slot(void *context, uint8_t slot,
    uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    fixture_t *fixture = context;
    if (slot > 1u || !fixture->present[slot]) {
        return false;
    }
    memcpy(record, fixture->slots[slot], OPENREF_CONFIG_SLOT_BYTES);
    return true;
}

static bool write_slot(void *context, uint8_t slot,
    const uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    fixture_t *fixture = context;
    if (slot > 1u) {
        return false;
    }
    memcpy(fixture->slots[slot], record, OPENREF_CONFIG_SLOT_BYTES);
    fixture->present[slot] = true;
    return true;
}

static bool set_voice(void *context, bool enabled)
{
    ((fixture_t *)context)->voice = enabled;
    return true;
}

static bool set_playback(void *context, bool enabled)
{
    fixture_t *fixture = context;
    if (enabled) {
        return openref_volume_manager_set_mute(fixture->volume,
                OPENREF_VOLUME_MUTE_SYSTEM_FAULT, false) &&
            openref_volume_manager_set_mute(fixture->volume,
                OPENREF_VOLUME_MUTE_STARTUP, false);
    }
    return openref_volume_manager_set_mute(fixture->volume,
        OPENREF_VOLUME_MUTE_SYSTEM_FAULT, true);
}

static bool set_network(void *context, bool enabled)
{
    ((fixture_t *)context)->network = enabled;
    return true;
}

int main(void)
{
    openref_volume_config_t volume_config = {
        .step_count = 4u,
        .safe_boot_step = 1u,
        .gain_q15 = {0u, 4096u, 8192u, 16384u},
    };
    openref_volume_manager_t volume;
    assert(openref_volume_manager_init(&volume, &volume_config));
    fixture_t fixture = {.volume = &volume};
    openref_config_backend_t config_backend = {read_slot, write_slot, &fixture};
    openref_settings_v1_constraints_t constraints = {
        4u, 1u, 1u, 1u, 1u, 1u,
    };
    openref_settings_v1_t defaults = {2u, 1u, 1u, 1u, 1u, 1u};
    openref_settings_runtime_t settings;
    assert(openref_settings_runtime_init(&settings, config_backend,
        &constraints, &defaults, &volume));
    assert(volume.requested_step == 2u);
    assert(openref_volume_manager_gain_q15(&volume) == 0u);

    openref_safety_gate_backend_t gates = {
        set_voice, set_playback, set_network, &fixture,
    };
    openref_startup_config_t startup_config = {100u, 100u};
    openref_system_runtime_t system;
    assert(openref_system_runtime_init(&system, &startup_config, gates, 0u));
    openref_safety_inputs_t safety = {.watchdog_healthy = true};
    openref_startup_inputs_t startup = {.power_safe = true};
    assert(openref_system_runtime_tick(&system, &startup, &safety, 1u));
    startup.rails_good = true;
    assert(openref_system_runtime_tick(&system, &startup, &safety, 2u));
    startup.authenticated_boot = true;
    startup.configuration_valid = true;
    startup.accessory_safe = true;
    startup.peer_healthy = true;
    assert(openref_system_runtime_tick(&system, &startup, &safety, 3u));
    assert(openref_volume_manager_gain_q15(&volume) == 0u);
    startup.crew_session_valid = true;
    assert(openref_system_runtime_tick(&system, &startup, &safety, 4u));
    assert(fixture.voice && fixture.network);
    assert(openref_volume_manager_gain_q15(&volume) == 8192u);

    safety.user_playback_mute = true;
    assert(openref_system_runtime_tick(&system, &startup, &safety, 5u));
    assert(openref_volume_manager_gain_q15(&volume) == 0u);
    assert(fixture.voice && fixture.network);
    return 0;
}
