#include <assert.h>
#include "openref_settings_v1.h"

static openref_settings_v1_constraints_t constraints(void)
{
    openref_settings_v1_constraints_t value = {
        .volume_step_count = 10u,
        .maximum_accessory_profile_id = 3u,
        .maximum_indicator_profile_id = 2u,
        .required_regulatory_region_id = 1u,
        .required_calibration_revision = 7u,
        .required_policy_revision = 4u,
    };
    return value;
}

static openref_settings_v1_t settings(void)
{
    openref_settings_v1_t value = {
        .preferred_volume_step = 3u,
        .accessory_profile_id = 2u,
        .indicator_profile_id = 1u,
        .regulatory_region_id = 1u,
        .calibration_revision = 7u,
        .policy_revision = 4u,
    };
    return value;
}

static void test_round_trip_and_explicit_wire(void)
{
    openref_settings_v1_constraints_t c = constraints();
    openref_settings_v1_t expected = settings();
    uint8_t wire[OPENREF_SETTINGS_V1_BYTES];
    assert(openref_settings_v1_encode(&expected, &c, wire));
    assert(wire[0] == 3u && wire[1] == 2u && wire[4] == 7u);
    for (uint8_t i = 12u; i < OPENREF_SETTINGS_V1_BYTES; i++) {
        assert(wire[i] == 0u);
    }
    openref_settings_v1_t decoded;
    assert(openref_settings_v1_decode(wire, &c, &decoded));
    assert(decoded.preferred_volume_step == expected.preferred_volume_step);
    assert(decoded.accessory_profile_id == expected.accessory_profile_id);
    assert(decoded.indicator_profile_id == expected.indicator_profile_id);
    assert(decoded.regulatory_region_id == expected.regulatory_region_id);
    assert(decoded.calibration_revision == expected.calibration_revision);
    assert(decoded.policy_revision == expected.policy_revision);
}

static void test_unsafe_or_unknown_values_reject(void)
{
    openref_settings_v1_constraints_t c = constraints();
    openref_settings_v1_t value = settings();
    uint8_t wire[OPENREF_SETTINGS_V1_BYTES];
    value.preferred_volume_step = 10u;
    assert(!openref_settings_v1_encode(&value, &c, wire));
    value = settings();
    value.regulatory_region_id = 2u;
    assert(!openref_settings_v1_encode(&value, &c, wire));
    value = settings();
    assert(openref_settings_v1_encode(&value, &c, wire));
    wire[12] = 1u;
    assert(!openref_settings_v1_decode(wire, &c, &value));
    wire[12] = 0u;
    wire[8] = 5u;
    assert(!openref_settings_v1_decode(wire, &c, &value));
}

static void test_profile_and_constraint_validation(void)
{
    openref_settings_v1_constraints_t c = constraints();
    openref_settings_v1_t value = settings();
    value.accessory_profile_id = 0u;
    assert(!openref_settings_v1_validate(&value, &c));
    value = settings();
    value.indicator_profile_id = 3u;
    assert(!openref_settings_v1_validate(&value, &c));
    c.volume_step_count = 0u;
    assert(!openref_settings_v1_validate(&value, &c));
}

int main(void)
{
    test_round_trip_and_explicit_wire();
    test_unsafe_or_unknown_values_reject();
    test_profile_and_constraint_validation();
    return 0;
}
