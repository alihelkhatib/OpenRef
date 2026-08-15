#include "openref_settings_v1.h"

#include <stddef.h>
#include <string.h>

static void write_u32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16);
    data[3] = (uint8_t)(value >> 24);
}

static uint32_t read_u32(const uint8_t *data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8) |
        ((uint32_t)data[2] << 16) | ((uint32_t)data[3] << 24);
}

static bool constraints_valid(const openref_settings_v1_constraints_t *c)
{
    return c != NULL && c->volume_step_count >= 1u &&
        c->volume_step_count <= 16u && c->maximum_accessory_profile_id != 0u &&
        c->maximum_indicator_profile_id != 0u &&
        c->required_regulatory_region_id != 0u &&
        c->required_calibration_revision != 0u &&
        c->required_policy_revision != 0u;
}

bool openref_settings_v1_validate(const openref_settings_v1_t *s,
    const openref_settings_v1_constraints_t *c)
{
    return s != NULL && constraints_valid(c) &&
        s->preferred_volume_step < c->volume_step_count &&
        s->accessory_profile_id >= 1u &&
        s->accessory_profile_id <= c->maximum_accessory_profile_id &&
        s->indicator_profile_id >= 1u &&
        s->indicator_profile_id <= c->maximum_indicator_profile_id &&
        s->regulatory_region_id == c->required_regulatory_region_id &&
        s->calibration_revision == c->required_calibration_revision &&
        s->policy_revision == c->required_policy_revision;
}

bool openref_settings_v1_encode(const openref_settings_v1_t *settings,
    const openref_settings_v1_constraints_t *constraints,
    uint8_t wire[OPENREF_SETTINGS_V1_BYTES])
{
    if (wire == NULL || !openref_settings_v1_validate(settings, constraints)) {
        return false;
    }
    memset(wire, 0, OPENREF_SETTINGS_V1_BYTES);
    wire[0] = settings->preferred_volume_step;
    wire[1] = settings->accessory_profile_id;
    wire[2] = settings->indicator_profile_id;
    wire[3] = settings->regulatory_region_id;
    write_u32(&wire[4], settings->calibration_revision);
    write_u32(&wire[8], settings->policy_revision);
    return true;
}

bool openref_settings_v1_decode(const uint8_t wire[OPENREF_SETTINGS_V1_BYTES],
    const openref_settings_v1_constraints_t *constraints,
    openref_settings_v1_t *settings)
{
    if (wire == NULL || settings == NULL || wire[12] != 0u || wire[13] != 0u ||
        wire[14] != 0u || wire[15] != 0u) {
        return false;
    }
    openref_settings_v1_t decoded = {
        .preferred_volume_step = wire[0],
        .accessory_profile_id = wire[1],
        .indicator_profile_id = wire[2],
        .regulatory_region_id = wire[3],
        .calibration_revision = read_u32(&wire[4]),
        .policy_revision = read_u32(&wire[8]),
    };
    if (!openref_settings_v1_validate(&decoded, constraints)) {
        return false;
    }
    *settings = decoded;
    return true;
}
