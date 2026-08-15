#include "openref_settings_runtime.h"

#include <stddef.h>
#include <string.h>

bool openref_settings_runtime_init(
    openref_settings_runtime_t *runtime,
    openref_config_backend_t backend,
    const openref_settings_v1_constraints_t *constraints,
    const openref_settings_v1_t *defaults,
    openref_volume_manager_t *volume)
{
    if (runtime == NULL || constraints == NULL || defaults == NULL ||
        volume == NULL || constraints->volume_step_count != volume->config.step_count ||
        !openref_settings_v1_validate(defaults, constraints)) {
        return false;
    }
    memset(runtime, 0, sizeof(*runtime));
    runtime->constraints = *constraints;
    if (!openref_config_store_init(&runtime->store, backend,
            OPENREF_SETTINGS_V1_SCHEMA_VERSION, OPENREF_SETTINGS_V1_BYTES)) {
        return false;
    }

    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES] = {0};
    openref_settings_v1_t selected = *defaults;
    if (openref_config_store_load(&runtime->store, payload)) {
        if (openref_settings_v1_decode(payload, constraints, &selected)) {
            runtime->source = OPENREF_SETTINGS_SOURCE_PERSISTED;
        } else {
            runtime->rejected_records++;
            selected = *defaults;
        }
    }
    if (!openref_volume_manager_restore_step(
            volume, selected.preferred_volume_step)) {
        return false;
    }
    runtime->active = selected;
    return true;
}

bool openref_settings_runtime_save(
    openref_settings_runtime_t *runtime,
    const openref_settings_v1_t *settings)
{
    if (runtime == NULL || settings == NULL) {
        return false;
    }
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES] = {0};
    if (!openref_settings_v1_encode(
            settings, &runtime->constraints, payload) ||
        !openref_config_store_save(&runtime->store, payload)) {
        return false;
    }
    runtime->active = *settings;
    runtime->source = OPENREF_SETTINGS_SOURCE_PERSISTED;
    return true;
}
