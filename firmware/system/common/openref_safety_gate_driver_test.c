#include <assert.h>

#include "openref_safety_gate_driver.h"

typedef struct {
    char log[32];
    uint8_t used;
    char fail_gate;
} backend_t;

static bool record(backend_t *backend, char gate, bool enabled)
{
    backend->log[backend->used++] = enabled ? gate : (char)(gate + ('a' - 'A'));
    return backend->fail_gate != gate;
}

static bool voice(void *context, bool enabled) { return record(context, 'V', enabled); }
static bool playback(void *context, bool enabled) { return record(context, 'P', enabled); }
static bool network(void *context, bool enabled) { return record(context, 'N', enabled); }

int main(void)
{
    backend_t backend = {0};
    openref_safety_gate_backend_t callbacks = {voice, playback, network, &backend};
    openref_safety_gate_driver_t driver;
    assert(openref_safety_gate_driver_init(&driver, callbacks));
    assert(backend.used == 3u && backend.log[0] == 'v' &&
        backend.log[1] == 'p' && backend.log[2] == 'n');

    openref_safety_output_t enabled = {
        .voice_uplink_enabled = true,
        .playback_enabled = true,
        .network_control_tx_enabled = true,
    };
    backend.used = 0u;
    assert(openref_safety_gate_driver_apply(&driver, &enabled));
    assert(backend.used == 3u && backend.log[0] == 'N' &&
        backend.log[1] == 'P' && backend.log[2] == 'V');

    openref_safety_output_t disabled = {0};
    backend.used = 0u;
    assert(openref_safety_gate_driver_apply(&driver, &disabled));
    assert(backend.used == 3u && backend.log[0] == 'v' &&
        backend.log[1] == 'p' && backend.log[2] == 'n');

    backend.used = 0u;
    backend.fail_gate = 'P';
    assert(!openref_safety_gate_driver_apply(&driver, &enabled));
    assert(driver.failures == 1u);
    assert(!driver.applied.voice_uplink_enabled &&
        !driver.applied.playback_enabled &&
        !driver.applied.network_control_tx_enabled);
    assert(backend.log[backend.used - 3u] == 'v' &&
        backend.log[backend.used - 2u] == 'p' &&
        backend.log[backend.used - 1u] == 'n');

    openref_safety_output_t impossible = {.voice_uplink_enabled = true};
    backend.fail_gate = 0;
    assert(!openref_safety_gate_driver_apply(&driver, &impossible));
    assert(driver.failures == 2u);
    return 0;
}
