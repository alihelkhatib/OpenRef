#include <assert.h>

#include "openref_accessory_monitor.h"

static openref_accessory_monitor_t make_monitor(void)
{
    openref_accessory_config_t config = {200u, 300u, 1700u, 1800u, 3u};
    openref_accessory_monitor_t monitor;
    assert(openref_accessory_monitor_init(&monitor, &config));
    return monitor;
}

static openref_accessory_output_t sample(openref_accessory_monitor_t *monitor,
    bool present, bool valid, uint16_t mv, uint8_t count)
{
    openref_accessory_output_t output = {0};
    for (uint8_t i = 0u; i < count; i++) {
        output = openref_accessory_monitor_update(monitor, present, valid, mv);
    }
    return output;
}

static void test_confirmation_and_immediate_safe_mute(void)
{
    openref_accessory_monitor_t monitor = make_monitor();
    openref_accessory_output_t out = sample(&monitor, true, true, 1000u, 3u);
    assert(out.state == OPENREF_ACCESSORY_OK && out.state_changed);
    assert(!out.mute_transmit && !out.mute_playback);
    out = sample(&monitor, false, true, 1000u, 1u);
    assert(out.state == OPENREF_ACCESSORY_OK);
    assert(out.mute_transmit && out.mute_playback);
    out = sample(&monitor, false, true, 1000u, 2u);
    assert(out.state == OPENREF_ACCESSORY_DISCONNECTED && out.state_changed);
}

static void test_short_open_and_hysteresis(void)
{
    openref_accessory_monitor_t monitor = make_monitor();
    sample(&monitor, true, true, 1000u, 3u);
    openref_accessory_output_t out = sample(&monitor, true, true, 100u, 3u);
    assert(out.state == OPENREF_ACCESSORY_MIC_SHORT && out.mute_transmit);
    out = sample(&monitor, true, true, 250u, 3u);
    assert(out.state == OPENREF_ACCESSORY_MIC_SHORT);
    out = sample(&monitor, true, true, 1000u, 3u);
    assert(out.state == OPENREF_ACCESSORY_OK);
    out = sample(&monitor, true, true, 1900u, 3u);
    assert(out.state == OPENREF_ACCESSORY_MIC_OPEN);
    out = sample(&monitor, true, true, 1750u, 3u);
    assert(out.state == OPENREF_ACCESSORY_MIC_OPEN);
    out = sample(&monitor, true, true, 1000u, 3u);
    assert(out.state == OPENREF_ACCESSORY_OK);
}

static void test_sensor_fault_mutes_both_paths(void)
{
    openref_accessory_monitor_t monitor = make_monitor();
    sample(&monitor, true, true, 1000u, 3u);
    openref_accessory_output_t out = sample(&monitor, true, false, 1000u, 1u);
    assert(out.mute_transmit && out.mute_playback);
    out = sample(&monitor, true, false, 1000u, 2u);
    assert(out.state == OPENREF_ACCESSORY_SENSOR_FAULT);
}

int main(void)
{
    test_confirmation_and_immediate_safe_mute();
    test_short_open_and_hysteresis();
    test_sensor_fault_mutes_both_paths();
    return 0;
}
