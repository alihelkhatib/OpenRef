#ifndef OPENREF_BOOT_STATE_STORE_H
#define OPENREF_BOOT_STATE_STORE_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_boot_policy.h"
#include "openref_config_store.h"

#define OPENREF_BOOT_STATE_STORE_SCHEMA_VERSION 1u
#define OPENREF_BOOT_STATE_STORE_PAYLOAD_BYTES 12u

typedef struct {
    openref_config_store_t records;
    uint32_t semantic_failures;
    bool initialized;
} openref_boot_state_store_t;

bool openref_boot_state_store_init(
    openref_boot_state_store_t *store,
    openref_config_backend_t backend);

bool openref_boot_state_store_load(
    openref_boot_state_store_t *store,
    openref_boot_state_t *state);

bool openref_boot_state_store_factory_initialize(
    openref_boot_state_store_t *store,
    const openref_boot_state_t *initial_state);

bool openref_boot_state_store_save(
    openref_boot_state_store_t *store,
    const openref_boot_state_t *state);

#endif
