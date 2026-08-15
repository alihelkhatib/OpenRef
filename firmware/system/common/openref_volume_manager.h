#ifndef OPENREF_VOLUME_MANAGER_H
#define OPENREF_VOLUME_MANAGER_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_VOLUME_MAX_STEPS 16u
#define OPENREF_VOLUME_MUTE_USER (1u << 0)
#define OPENREF_VOLUME_MUTE_STARTUP (1u << 1)
#define OPENREF_VOLUME_MUTE_HEADSET_FAULT (1u << 2)
#define OPENREF_VOLUME_MUTE_SYSTEM_FAULT (1u << 3)
#define OPENREF_VOLUME_MUTE_SHUTDOWN (1u << 4)

typedef struct {
    uint8_t step_count;
    uint8_t safe_boot_step;
    uint16_t gain_q15[OPENREF_VOLUME_MAX_STEPS];
} openref_volume_config_t;

typedef struct {
    openref_volume_config_t config;
    uint8_t requested_step;
    uint8_t active_ceiling_step;
    uint32_t mute_reasons;
    uint32_t increases;
    uint32_t decreases;
    uint32_t ceiling_reductions;
    uint32_t mute_transitions;
} openref_volume_manager_t;

bool openref_volume_manager_init(
    openref_volume_manager_t *manager,
    const openref_volume_config_t *config);

bool openref_volume_manager_step(
    openref_volume_manager_t *manager,
    int8_t direction);

bool openref_volume_manager_set_ceiling(
    openref_volume_manager_t *manager,
    uint8_t ceiling_step);

bool openref_volume_manager_restore_step(
    openref_volume_manager_t *manager,
    uint8_t requested_step);

bool openref_volume_manager_set_mute(
    openref_volume_manager_t *manager,
    uint32_t reason,
    bool enabled);

uint16_t openref_volume_manager_gain_q15(
    const openref_volume_manager_t *manager);

#endif
