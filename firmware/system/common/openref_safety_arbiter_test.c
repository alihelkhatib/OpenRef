#include <assert.h>
#include <stddef.h>

#include "openref_peer_supervisor.h"
#include "openref_power_supervisor.h"
#include "openref_safety_arbiter.h"
#include "openref_startup_supervisor.h"

static openref_safety_inputs_t operational(void)
{
    openref_safety_inputs_t inputs = {
        .startup_actions = OPENREF_STARTUP_ACTION_ENABLE_RAILS |
            OPENREF_STARTUP_ACTION_RELEASE_RESETS |
            OPENREF_STARTUP_ACTION_PERMIT_RF_TX,
        .watchdog_healthy = true,
    };
    return inputs;
}

static void test_nominal_and_independent_audio_faults(void)
{
    openref_safety_inputs_t in = operational();
    openref_safety_output_t out = openref_safety_arbitrate(&in);
    assert(out.voice_uplink_enabled && out.playback_enabled &&
           out.network_control_tx_enabled);
    in.accessory_mute_transmit = true;
    out = openref_safety_arbitrate(&in);
    assert(!out.voice_uplink_enabled && out.playback_enabled);
    assert(out.network_control_tx_enabled);
    in.accessory_mute_transmit = false;
    in.peer_actions = OPENREF_PEER_ACTION_MUTE_AUDIO;
    out = openref_safety_arbitrate(&in);
    assert(!out.voice_uplink_enabled && !out.playback_enabled);
    assert(out.network_control_tx_enabled);
}

static void test_global_interlocks_cannot_be_overridden(void)
{
    openref_safety_inputs_t in = operational();
    in.update_active = true;
    openref_safety_output_t out = openref_safety_arbitrate(&in);
    assert(!out.voice_uplink_enabled && !out.playback_enabled &&
           !out.network_control_tx_enabled);
    in = operational();
    in.power_actions = OPENREF_POWER_ACTION_REQUEST_SHUTDOWN;
    out = openref_safety_arbitrate(&in);
    assert((out.radio_inhibit_reasons & OPENREF_INHIBIT_POWER) != 0u);
    in = operational();
    in.watchdog_healthy = false;
    out = openref_safety_arbitrate(&in);
    assert((out.radio_inhibit_reasons & OPENREF_INHIBIT_WATCHDOG) != 0u);
    out = openref_safety_arbitrate(NULL);
    assert(!out.voice_uplink_enabled && !out.playback_enabled &&
           !out.network_control_tx_enabled);
}

static void test_every_inhibit_bit_preserves_enable_invariants(void)
{
    for (uint16_t combination = 0u; combination < 512u; combination++) {
        openref_safety_inputs_t in = operational();
        in.power_actions = (combination & 1u) != 0u
            ? OPENREF_POWER_ACTION_MUTE_AUDIO : 0u;
        if ((combination & 2u) != 0u) {
            in.startup_actions &= (uint32_t)~OPENREF_STARTUP_ACTION_PERMIT_RF_TX;
        }
        in.accessory_mute_transmit = (combination & 4u) != 0u;
        in.peer_actions = (combination & 8u) != 0u
            ? OPENREF_PEER_ACTION_MUTE_AUDIO : 0u;
        in.watchdog_healthy = (combination & 16u) == 0u;
        in.update_active = (combination & 32u) != 0u;
        in.privileged_service_active = (combination & 64u) != 0u;
        in.user_transmit_mute = (combination & 128u) != 0u;
        in.system_fault = (combination & 256u) != 0u;
        openref_safety_output_t out = openref_safety_arbitrate(&in);
        assert(out.voice_uplink_enabled ==
            (out.transmit_mute_reasons == 0u &&
             out.radio_inhibit_reasons == 0u));
        assert(out.playback_enabled == (out.playback_mute_reasons == 0u));
        assert(out.network_control_tx_enabled ==
            (out.radio_inhibit_reasons == 0u));
    }
}

int main(void)
{
    test_nominal_and_independent_audio_faults();
    test_global_interlocks_cannot_be_overridden();
    test_every_inhibit_bit_preserves_enable_invariants();
    return 0;
}
