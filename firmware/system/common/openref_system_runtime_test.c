#include <assert.h>

#include "openref_system_runtime.h"

typedef struct {
    bool voice;
    bool playback;
    bool network;
    bool fail_voice_enable;
} backend_t;

static bool set_voice(void *context, bool enabled)
{
    backend_t *backend = context;
    if (enabled && backend->fail_voice_enable) {
        return false;
    }
    backend->voice = enabled;
    return true;
}

static bool set_playback(void *context, bool enabled)
{
    ((backend_t *)context)->playback = enabled;
    return true;
}

static bool set_network(void *context, bool enabled)
{
    ((backend_t *)context)->network = enabled;
    return true;
}

int main(void)
{
    backend_t backend = {0};
    openref_safety_gate_backend_t gate_backend = {
        set_voice, set_playback, set_network, &backend,
    };
    openref_startup_config_t config = {100u, 100u};
    openref_system_runtime_t runtime;
    assert(openref_system_runtime_init(&runtime, &config, gate_backend, 0u));
    assert(!backend.voice && !backend.playback && !backend.network);

    openref_safety_inputs_t safety = {.watchdog_healthy = true};
    openref_startup_inputs_t startup = {.power_safe = true};
    assert(openref_system_runtime_tick(&runtime, &startup, &safety, 1u));
    assert(!backend.voice && !backend.playback && !backend.network);
    startup.rails_good = true;
    assert(openref_system_runtime_tick(&runtime, &startup, &safety, 2u));
    startup.authenticated_boot = true;
    startup.configuration_valid = true;
    startup.accessory_safe = true;
    startup.peer_healthy = true;
    assert(openref_system_runtime_tick(&runtime, &startup, &safety, 3u));
    assert(!backend.voice && !backend.playback && !backend.network);
    startup.crew_session_valid = true;
    assert(openref_system_runtime_tick(&runtime, &startup, &safety, 4u));
    assert(backend.voice && backend.playback && backend.network);

    safety.user_transmit_mute = true;
    assert(openref_system_runtime_tick(&runtime, &startup, &safety, 5u));
    assert(!backend.voice && backend.playback && backend.network);
    safety.user_transmit_mute = false;
    backend.fail_voice_enable = true;
    assert(!openref_system_runtime_tick(&runtime, &startup, &safety, 6u));
    assert(!backend.voice && !backend.playback && !backend.network);
    assert(runtime.actuation_fault_latched && runtime.actuation_faults == 1u);
    backend.fail_voice_enable = false;
    assert(openref_system_runtime_tick(&runtime, &startup, &safety, 7u));
    assert(!backend.voice && !backend.playback && !backend.network);
    assert((runtime.output.radio_inhibit_reasons &
        OPENREF_INHIBIT_SYSTEM_FAULT) != 0u);
    return 0;
}
