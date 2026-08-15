#ifndef OPENREF_SETTINGS_RUNTIME_H
#define OPENREF_SETTINGS_RUNTIME_H

#include <stdbool.h>

#include "openref_config_store.h"
#include "openref_settings_v1.h"
#include "openref_volume_manager.h"

typedef enum {
    OPENREF_SETTINGS_SOURCE_DEFAULTS = 0,
    OPENREF_SETTINGS_SOURCE_PERSISTED
} openref_settings_source_t;

typedef struct {
    openref_config_store_t store;
    openref_settings_v1_constraints_t constraints;
    openref_settings_v1_t active;
    openref_settings_source_t source;
    uint32_t rejected_records;
} openref_settings_runtime_t;

bool openref_settings_runtime_init(
    openref_settings_runtime_t *runtime,
    openref_config_backend_t backend,
    const openref_settings_v1_constraints_t *constraints,
    const openref_settings_v1_t *defaults,
    openref_volume_manager_t *volume);

bool openref_settings_runtime_save(
    openref_settings_runtime_t *runtime,
    const openref_settings_v1_t *settings);

#endif
