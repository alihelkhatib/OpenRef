#ifndef OPENREF_DEVICE_RECORD_STORE_H
#define OPENREF_DEVICE_RECORD_STORE_H

#include <stdbool.h>

#include "openref_config_store.h"
#include "openref_device_lifecycle.h"

#define OPENREF_DEVICE_RECORD_STORE_SCHEMA_VERSION 1u
#define OPENREF_DEVICE_RECORD_STORE_PAYLOAD_BYTES 36u

typedef struct {
    openref_config_store_t records;
    uint32_t semantic_failures;
    bool initialized;
} openref_device_record_store_t;

bool openref_device_record_store_init(
    openref_device_record_store_t *store,
    openref_config_backend_t backend);

bool openref_device_record_store_load(
    openref_device_record_store_t *store,
    openref_device_record_t *record);

bool openref_device_record_store_factory_initialize(
    openref_device_record_store_t *store);

bool openref_device_record_store_save(
    openref_device_record_store_t *store,
    const openref_device_record_t *record);

bool openref_device_record_store_callback(
    void *context,
    const openref_device_record_t *record);

#endif
