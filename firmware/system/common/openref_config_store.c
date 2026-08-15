#include "openref_config_store.h"

#include <stddef.h>
#include <string.h>

#define HEADER_BYTES 12u
#define CRC_OFFSET (OPENREF_CONFIG_SLOT_BYTES - 4u)

static void write_u16(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
}

static void write_u32(uint8_t *data, uint32_t value)
{
    for (uint8_t i = 0u; i < 4u; i++) {
        data[i] = (uint8_t)(value >> (8u * i));
    }
}

static uint16_t read_u16(const uint8_t *data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8);
}

static uint32_t read_u32(const uint8_t *data)
{
    uint32_t value = 0u;
    for (uint8_t i = 0u; i < 4u; i++) {
        value |= (uint32_t)data[i] << (8u * i);
    }
    return value;
}

static uint32_t crc32(const uint8_t *data, uint16_t length)
{
    uint32_t crc = 0xffffffffu;
    for (uint16_t i = 0u; i < length; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0u; bit < 8u; bit++) {
            crc = (crc >> 1) ^ ((crc & 1u) != 0u ? 0xedb88320u : 0u);
        }
    }
    return ~crc;
}

static bool decode(
    const openref_config_store_t *store,
    const uint8_t record[OPENREF_CONFIG_SLOT_BYTES],
    uint32_t *generation)
{
    if (read_u32(&record[0]) != OPENREF_CONFIG_MAGIC ||
        read_u16(&record[4]) != store->schema_version ||
        read_u16(&record[6]) != store->payload_length ||
        read_u32(&record[CRC_OFFSET]) != crc32(record, CRC_OFFSET)) {
        return false;
    }
    *generation = read_u32(&record[8]);
    return *generation != 0u;
}

static bool newer(uint32_t candidate, uint32_t reference)
{
    return (int32_t)(candidate - reference) > 0;
}

bool openref_config_store_init(
    openref_config_store_t *store,
    openref_config_backend_t backend,
    uint16_t schema_version,
    uint16_t payload_length)
{
    if (store == NULL || backend.read_slot == NULL || backend.write_slot == NULL ||
        schema_version == 0u || payload_length == 0u ||
        payload_length > OPENREF_CONFIG_MAX_PAYLOAD_BYTES) {
        return false;
    }
    memset(store, 0, sizeof(*store));
    store->backend = backend;
    store->schema_version = schema_version;
    store->payload_length = payload_length;
    return true;
}

bool openref_config_store_load(
    openref_config_store_t *store,
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES])
{
    if (store == NULL || payload == NULL) {
        return false;
    }
    uint8_t records[2][OPENREF_CONFIG_SLOT_BYTES];
    uint32_t generations[2] = {0u, 0u};
    bool valid[2] = {false, false};
    for (uint8_t slot = 0u; slot < 2u; slot++) {
        valid[slot] = store->backend.read_slot(
            store->backend.context, slot, records[slot]) &&
            decode(store, records[slot], &generations[slot]);
    }
    if (!valid[0] && !valid[1]) {
        store->load_failures++;
        store->loaded = false;
        return false;
    }
    uint8_t selected = valid[1] &&
        (!valid[0] || newer(generations[1], generations[0])) ? 1u : 0u;
    memcpy(payload, &records[selected][HEADER_BYTES], store->payload_length);
    store->generation = generations[selected];
    store->active_slot = selected;
    store->loaded = true;
    return true;
}

bool openref_config_store_save(
    openref_config_store_t *store,
    const uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES])
{
    if (store == NULL || payload == NULL || store->generation == UINT32_MAX) {
        return false;
    }
    uint32_t next_generation = store->loaded ? store->generation + 1u : 1u;
    uint8_t target_slot = store->loaded ? (uint8_t)(store->active_slot ^ 1u) : 0u;
    uint8_t record[OPENREF_CONFIG_SLOT_BYTES] = {0};
    write_u32(&record[0], OPENREF_CONFIG_MAGIC);
    write_u16(&record[4], store->schema_version);
    write_u16(&record[6], store->payload_length);
    write_u32(&record[8], next_generation);
    memcpy(&record[HEADER_BYTES], payload, store->payload_length);
    write_u32(&record[CRC_OFFSET], crc32(record, CRC_OFFSET));
    if (!store->backend.write_slot(store->backend.context, target_slot, record)) {
        store->write_failures++;
        return false;
    }
    uint8_t verify[OPENREF_CONFIG_SLOT_BYTES];
    uint32_t verified_generation = 0u;
    if (!store->backend.read_slot(store->backend.context, target_slot, verify) ||
        !decode(store, verify, &verified_generation) ||
        verified_generation != next_generation ||
        memcmp(record, verify, sizeof(record)) != 0) {
        store->write_failures++;
        return false;
    }
    store->generation = next_generation;
    store->active_slot = target_slot;
    store->loaded = true;
    return true;
}
