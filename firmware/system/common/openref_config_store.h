#ifndef OPENREF_CONFIG_STORE_H
#define OPENREF_CONFIG_STORE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_CONFIG_MAGIC 0x4346524fu
#define OPENREF_CONFIG_MAX_PAYLOAD_BYTES 64u
#define OPENREF_CONFIG_SLOT_BYTES 80u

typedef bool (*openref_config_read_slot_fn)(
    void *context, uint8_t slot, uint8_t record[OPENREF_CONFIG_SLOT_BYTES]);
typedef bool (*openref_config_write_slot_fn)(
    void *context, uint8_t slot,
    const uint8_t record[OPENREF_CONFIG_SLOT_BYTES]);

typedef struct {
    openref_config_read_slot_fn read_slot;
    openref_config_write_slot_fn write_slot;
    void *context;
} openref_config_backend_t;

typedef struct {
    openref_config_backend_t backend;
    uint16_t schema_version;
    uint16_t payload_length;
    uint32_t generation;
    uint8_t active_slot;
    uint32_t load_failures;
    uint32_t write_failures;
    bool loaded;
} openref_config_store_t;

bool openref_config_store_init(
    openref_config_store_t *store,
    openref_config_backend_t backend,
    uint16_t schema_version,
    uint16_t payload_length);

bool openref_config_store_load(
    openref_config_store_t *store,
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES]);

bool openref_config_store_save(
    openref_config_store_t *store,
    const uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES]);

#ifdef __cplusplus
}
#endif

#endif
