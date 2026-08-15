#include <assert.h>
#include <string.h>

#include "openref_settings_runtime.h"

typedef struct {
    uint8_t slots[2][OPENREF_CONFIG_SLOT_BYTES];
    bool present[2];
} memory_backend_t;

static bool read_slot(void *context, uint8_t slot,
    uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    memory_backend_t *memory = context;
    if (slot > 1u || !memory->present[slot]) {
        return false;
    }
    memcpy(record, memory->slots[slot], OPENREF_CONFIG_SLOT_BYTES);
    return true;
}

static bool write_slot(void *context, uint8_t slot,
    const uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    memory_backend_t *memory = context;
    if (slot > 1u) {
        return false;
    }
    memcpy(memory->slots[slot], record, OPENREF_CONFIG_SLOT_BYTES);
    memory->present[slot] = true;
    return true;
}

static openref_volume_config_t volume_config(void)
{
    openref_volume_config_t value = {
        .step_count = 5u,
        .safe_boot_step = 1u,
        .gain_q15 = {0u, 4096u, 8192u, 16384u, 32768u},
    };
    return value;
}

static openref_settings_v1_constraints_t constraints(void)
{
    openref_settings_v1_constraints_t value = {
        .volume_step_count = 5u,
        .maximum_accessory_profile_id = 2u,
        .maximum_indicator_profile_id = 2u,
        .required_regulatory_region_id = 1u,
        .required_calibration_revision = 7u,
        .required_policy_revision = 4u,
    };
    return value;
}

static openref_settings_v1_t defaults(void)
{
    openref_settings_v1_t value = {1u, 1u, 1u, 1u, 7u, 4u};
    return value;
}

int main(void)
{
    memory_backend_t memory = {0};
    openref_config_backend_t backend = {read_slot, write_slot, &memory};
    openref_volume_config_t vc = volume_config();
    openref_volume_manager_t volume;
    assert(openref_volume_manager_init(&volume, &vc));
    openref_settings_v1_constraints_t c = constraints();
    openref_settings_v1_t d = defaults();
    openref_settings_runtime_t runtime;
    assert(openref_settings_runtime_init(&runtime, backend, &c, &d, &volume));
    assert(runtime.source == OPENREF_SETTINGS_SOURCE_DEFAULTS);
    assert(volume.requested_step == 1u);
    assert((volume.mute_reasons & OPENREF_VOLUME_MUTE_STARTUP) != 0u);

    openref_settings_v1_t saved = d;
    saved.preferred_volume_step = 4u;
    assert(openref_settings_runtime_save(&runtime, &saved));
    assert(openref_volume_manager_init(&volume, &vc));
    assert(openref_settings_runtime_init(&runtime, backend, &c, &d, &volume));
    assert(runtime.source == OPENREF_SETTINGS_SOURCE_PERSISTED);
    assert(volume.requested_step == 4u);
    assert(openref_volume_manager_gain_q15(&volume) == 0u);

    memory.slots[runtime.store.active_slot][20] ^= 1u;
    assert(openref_volume_manager_init(&volume, &vc));
    assert(openref_settings_runtime_init(&runtime, backend, &c, &d, &volume));
    assert(runtime.source == OPENREF_SETTINGS_SOURCE_DEFAULTS);
    assert(volume.requested_step == 1u);

    c.volume_step_count = 4u;
    assert(!openref_settings_runtime_init(&runtime, backend, &c, &d, &volume));
    return 0;
}
