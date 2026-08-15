#include <assert.h>
#include <stdint.h>

#include "openref_volume_manager.h"

int main(void)
{
    const openref_volume_config_t config = {
        .step_count = 5u,
        .safe_boot_step = 2u,
        .gain_q15 = {0u, 4096u, 8192u, 16384u, 32768u},
    };
    openref_volume_manager_t manager;
    assert(openref_volume_manager_init(&manager, &config));
    assert(openref_volume_manager_gain_q15(&manager) == 0u);
    assert(openref_volume_manager_set_mute(
        &manager, OPENREF_VOLUME_MUTE_STARTUP, false));
    assert(openref_volume_manager_gain_q15(&manager) == 8192u);
    assert(openref_volume_manager_step(&manager, 1));
    assert(openref_volume_manager_gain_q15(&manager) == 16384u);
    assert(openref_volume_manager_set_ceiling(&manager, 1u));
    assert(manager.requested_step == 1u);
    assert(manager.ceiling_reductions == 1u);
    assert(!openref_volume_manager_step(&manager, 1));
    assert(openref_volume_manager_gain_q15(&manager) == 4096u);
    assert(openref_volume_manager_set_ceiling(&manager, 4u));
    assert(manager.requested_step == 1u);
    assert(openref_volume_manager_set_mute(
        &manager, OPENREF_VOLUME_MUTE_HEADSET_FAULT, true));
    assert(openref_volume_manager_gain_q15(&manager) == 0u);
    assert(openref_volume_manager_set_mute(
        &manager, OPENREF_VOLUME_MUTE_USER, true));
    assert(openref_volume_manager_set_mute(
        &manager, OPENREF_VOLUME_MUTE_HEADSET_FAULT, false));
    assert(openref_volume_manager_gain_q15(&manager) == 0u);
    assert(openref_volume_manager_set_mute(
        &manager, OPENREF_VOLUME_MUTE_USER, false));
    assert(openref_volume_manager_gain_q15(&manager) == 4096u);
    assert(manager.mute_transitions == 3u);
    assert(openref_volume_manager_set_mute(
        &manager, OPENREF_VOLUME_MUTE_STARTUP, true));
    assert(openref_volume_manager_restore_step(&manager, 3u));
    assert(manager.requested_step == 3u);
    assert(openref_volume_manager_gain_q15(&manager) == 0u);
    assert(openref_volume_manager_set_ceiling(&manager, 2u));
    assert(openref_volume_manager_restore_step(&manager, 4u));
    assert(manager.requested_step == 2u);
    assert(!openref_volume_manager_restore_step(&manager, 5u));
    return 0;
}
