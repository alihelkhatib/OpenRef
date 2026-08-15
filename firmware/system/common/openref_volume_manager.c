#include "openref_volume_manager.h"

#include <stddef.h>

bool openref_volume_manager_init(
    openref_volume_manager_t *manager,
    const openref_volume_config_t *config)
{
    if (manager == NULL || config == NULL || config->step_count == 0u ||
        config->step_count > OPENREF_VOLUME_MAX_STEPS ||
        config->safe_boot_step >= config->step_count || config->gain_q15[0] != 0u) {
        return false;
    }
    for (uint8_t index = 0u; index < config->step_count; index++) {
        if (config->gain_q15[index] > 32768u ||
            (index > 0u && config->gain_q15[index] < config->gain_q15[index - 1u])) {
            return false;
        }
    }
    *manager = (openref_volume_manager_t){0};
    manager->config = *config;
    manager->requested_step = config->safe_boot_step;
    manager->active_ceiling_step = (uint8_t)(config->step_count - 1u);
    manager->mute_reasons = OPENREF_VOLUME_MUTE_STARTUP;
    return true;
}

bool openref_volume_manager_step(
    openref_volume_manager_t *manager,
    int8_t direction)
{
    if (manager == NULL || (direction != -1 && direction != 1)) {
        return false;
    }
    if (direction > 0) {
        if (manager->requested_step >= manager->active_ceiling_step) {
            return false;
        }
        manager->requested_step++;
        manager->increases++;
    } else {
        if (manager->requested_step == 0u) {
            return false;
        }
        manager->requested_step--;
        manager->decreases++;
    }
    return true;
}

bool openref_volume_manager_set_ceiling(
    openref_volume_manager_t *manager,
    uint8_t ceiling_step)
{
    if (manager == NULL || ceiling_step >= manager->config.step_count) {
        return false;
    }
    manager->active_ceiling_step = ceiling_step;
    if (manager->requested_step > ceiling_step) {
        manager->requested_step = ceiling_step;
        manager->ceiling_reductions++;
    }
    return true;
}

bool openref_volume_manager_restore_step(
    openref_volume_manager_t *manager,
    uint8_t requested_step)
{
    if (manager == NULL || requested_step >= manager->config.step_count) {
        return false;
    }
    manager->requested_step = requested_step > manager->active_ceiling_step ?
        manager->active_ceiling_step : requested_step;
    return true;
}

bool openref_volume_manager_set_mute(
    openref_volume_manager_t *manager,
    uint32_t reason,
    bool enabled)
{
    const uint32_t valid_reasons = OPENREF_VOLUME_MUTE_USER |
        OPENREF_VOLUME_MUTE_STARTUP | OPENREF_VOLUME_MUTE_HEADSET_FAULT |
        OPENREF_VOLUME_MUTE_SYSTEM_FAULT | OPENREF_VOLUME_MUTE_SHUTDOWN;
    if (manager == NULL || reason == 0u || (reason & ~valid_reasons) != 0u) {
        return false;
    }
    uint32_t previous = manager->mute_reasons;
    if (enabled) {
        manager->mute_reasons |= reason;
    } else {
        manager->mute_reasons &= ~reason;
    }
    if ((previous == 0u) != (manager->mute_reasons == 0u)) {
        manager->mute_transitions++;
    }
    return true;
}

uint16_t openref_volume_manager_gain_q15(
    const openref_volume_manager_t *manager)
{
    if (manager == NULL || manager->mute_reasons != 0u) {
        return 0u;
    }
    return manager->config.gain_q15[manager->requested_step];
}
