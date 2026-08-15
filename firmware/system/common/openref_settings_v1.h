#ifndef OPENREF_SETTINGS_V1_H
#define OPENREF_SETTINGS_V1_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_SETTINGS_V1_SCHEMA_VERSION 1u
#define OPENREF_SETTINGS_V1_BYTES 16u

typedef struct {
    uint8_t preferred_volume_step;
    uint8_t accessory_profile_id;
    uint8_t indicator_profile_id;
    uint8_t regulatory_region_id;
    uint32_t calibration_revision;
    uint32_t policy_revision;
} openref_settings_v1_t;

typedef struct {
    uint8_t volume_step_count;
    uint8_t maximum_accessory_profile_id;
    uint8_t maximum_indicator_profile_id;
    uint8_t required_regulatory_region_id;
    uint32_t required_calibration_revision;
    uint32_t required_policy_revision;
} openref_settings_v1_constraints_t;

bool openref_settings_v1_validate(
    const openref_settings_v1_t *settings,
    const openref_settings_v1_constraints_t *constraints);

bool openref_settings_v1_encode(
    const openref_settings_v1_t *settings,
    const openref_settings_v1_constraints_t *constraints,
    uint8_t wire[OPENREF_SETTINGS_V1_BYTES]);

bool openref_settings_v1_decode(
    const uint8_t wire[OPENREF_SETTINGS_V1_BYTES],
    const openref_settings_v1_constraints_t *constraints,
    openref_settings_v1_t *settings);

#endif
