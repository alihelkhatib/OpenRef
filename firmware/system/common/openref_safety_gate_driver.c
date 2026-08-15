#include "openref_safety_gate_driver.h"

#include <stddef.h>
#include <string.h>

static void force_safe(openref_safety_gate_driver_t *driver)
{
    (void)driver->backend.set_voice_uplink(driver->backend.context, false);
    (void)driver->backend.set_playback(driver->backend.context, false);
    (void)driver->backend.set_network_control_tx(driver->backend.context, false);
    driver->applied = (openref_safety_output_t){0};
}

bool openref_safety_gate_driver_init(
    openref_safety_gate_driver_t *driver,
    openref_safety_gate_backend_t backend)
{
    if (driver == NULL || backend.set_voice_uplink == NULL ||
        backend.set_playback == NULL || backend.set_network_control_tx == NULL) {
        return false;
    }
    memset(driver, 0, sizeof(*driver));
    driver->backend = backend;
    force_safe(driver);
    driver->initialized = true;
    return true;
}

bool openref_safety_gate_driver_apply(
    openref_safety_gate_driver_t *driver,
    const openref_safety_output_t *desired)
{
    if (driver == NULL || !driver->initialized || desired == NULL ||
        (desired->voice_uplink_enabled &&
         !desired->network_control_tx_enabled)) {
        if (driver != NULL && driver->initialized) {
            driver->failures++;
            force_safe(driver);
        }
        return false;
    }
    bool ok = true;
    if (driver->applied.voice_uplink_enabled && !desired->voice_uplink_enabled) {
        ok = driver->backend.set_voice_uplink(driver->backend.context, false);
    }
    if (ok && driver->applied.playback_enabled && !desired->playback_enabled) {
        ok = driver->backend.set_playback(driver->backend.context, false);
    }
    if (ok && driver->applied.network_control_tx_enabled &&
        !desired->network_control_tx_enabled) {
        ok = driver->backend.set_network_control_tx(driver->backend.context, false);
    }
    if (ok && !driver->applied.network_control_tx_enabled &&
        desired->network_control_tx_enabled) {
        ok = driver->backend.set_network_control_tx(driver->backend.context, true);
    }
    if (ok && !driver->applied.playback_enabled && desired->playback_enabled) {
        ok = driver->backend.set_playback(driver->backend.context, true);
    }
    if (ok && !driver->applied.voice_uplink_enabled &&
        desired->voice_uplink_enabled) {
        ok = driver->backend.set_voice_uplink(driver->backend.context, true);
    }
    if (!ok) {
        driver->failures++;
        force_safe(driver);
        return false;
    }
    if (driver->applied.voice_uplink_enabled != desired->voice_uplink_enabled ||
        driver->applied.playback_enabled != desired->playback_enabled ||
        driver->applied.network_control_tx_enabled !=
            desired->network_control_tx_enabled) {
        driver->transitions++;
    }
    driver->applied = *desired;
    return true;
}
