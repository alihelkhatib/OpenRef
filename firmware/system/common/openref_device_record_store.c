#include "openref_device_record_store.h"

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

static void encode(const openref_device_record_t *record,
                   uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES])
{
    memset(payload, 0, OPENREF_CONFIG_MAX_PAYLOAD_BYTES);
    payload[0] = (uint8_t)record->state;
    memcpy(&payload[4], record->device_id, OPENREF_DEVICE_ID_BYTES);
    memcpy(&payload[20], record->identity_fingerprint,
           OPENREF_IDENTITY_FINGERPRINT_BYTES);
    write_u32(&payload[28], record->generation);
    write_u32(&payload[32], record->failure_code);
}

static bool decode(const uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES],
                   openref_device_record_t *record)
{
    openref_device_record_t decoded;
    if (payload[1] != 0u || payload[2] != 0u || payload[3] != 0u) {
        return false;
    }
    memset(&decoded, 0, sizeof(decoded));
    decoded.state = (openref_device_state_t)payload[0];
    memcpy(decoded.device_id, &payload[4], OPENREF_DEVICE_ID_BYTES);
    memcpy(decoded.identity_fingerprint, &payload[20],
           OPENREF_IDENTITY_FINGERPRINT_BYTES);
    decoded.generation = read_u32(&payload[28]);
    decoded.failure_code = read_u32(&payload[32]);
    if (!openref_device_record_valid(&decoded)) {
        return false;
    }
    *record = decoded;
    return true;
}

bool openref_device_record_store_init(
    openref_device_record_store_t *store,
    openref_config_backend_t backend)
{
    if (store == NULL) return false;
    memset(store, 0, sizeof(*store));
    if (!openref_config_store_init(
            &store->records, backend,
            OPENREF_DEVICE_RECORD_STORE_SCHEMA_VERSION,
            OPENREF_DEVICE_RECORD_STORE_PAYLOAD_BYTES)) {
        return false;
    }
    store->initialized = true;
    return true;
}

bool openref_device_record_store_load(
    openref_device_record_store_t *store,
    openref_device_record_t *record)
{
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];
    if (store == NULL || record == NULL || !store->initialized ||
        !openref_config_store_load(&store->records, payload) ||
        !decode(payload, record)) {
        if (store != NULL) {
            store->semantic_failures++;
            store->records.loaded = false;
        }
        return false;
    }
    return true;
}

bool openref_device_record_store_factory_initialize(
    openref_device_record_store_t *store)
{
    openref_device_record_t blank;
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];
    if (store == NULL || !store->initialized || store->records.loaded) {
        return false;
    }
    memset(&blank, 0, sizeof(blank));
    encode(&blank, payload);
    return openref_config_store_save(&store->records, payload);
}

bool openref_device_record_store_save(
    openref_device_record_store_t *store,
    const openref_device_record_t *record)
{
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];
    if (store == NULL || record == NULL || !store->initialized ||
        !store->records.loaded || !openref_device_record_valid(record)) {
        if (store != NULL) store->semantic_failures++;
        return false;
    }
    encode(record, payload);
    return openref_config_store_save(&store->records, payload);
}

bool openref_device_record_store_callback(
    void *context,
    const openref_device_record_t *record)
{
    return openref_device_record_store_save(context, record);
}
