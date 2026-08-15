#include "openref_boot_state_store.h"

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

static void encode(const openref_boot_state_t *state,
                   uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES])
{
    memset(payload, 0, OPENREF_CONFIG_MAX_PAYLOAD_BYTES);
    write_u32(&payload[0], state->record_version);
    write_u32(&payload[4], state->minimum_version);
    payload[8] = state->confirmed_slot;
    payload[9] = state->pending_slot;
    payload[10] = state->pending_attempts;
}

static bool decode(const uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES],
                   openref_boot_state_t *state)
{
    if (payload[11] != 0u) {
        return false;
    }
    openref_boot_state_t decoded = {
        .record_version = read_u32(&payload[0]),
        .minimum_version = read_u32(&payload[4]),
        .confirmed_slot = payload[8],
        .pending_slot = payload[9],
        .pending_attempts = payload[10],
    };
    if (!openref_boot_policy_state_valid(&decoded) ||
        (decoded.pending_slot == OPENREF_BOOT_NO_SLOT &&
         decoded.pending_attempts != 0u) ||
        decoded.pending_slot == decoded.confirmed_slot) {
        return false;
    }
    *state = decoded;
    return true;
}

bool openref_boot_state_store_init(
    openref_boot_state_store_t *store,
    openref_config_backend_t backend)
{
    if (store == NULL) {
        return false;
    }
    memset(store, 0, sizeof(*store));
    if (!openref_config_store_init(
            &store->records, backend, OPENREF_BOOT_STATE_STORE_SCHEMA_VERSION,
            OPENREF_BOOT_STATE_STORE_PAYLOAD_BYTES)) {
        return false;
    }
    store->initialized = true;
    return true;
}

bool openref_boot_state_store_load(
    openref_boot_state_store_t *store,
    openref_boot_state_t *state)
{
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];
    if (store == NULL || state == NULL || !store->initialized ||
        !openref_config_store_load(&store->records, payload) ||
        !decode(payload, state)) {
        if (store != NULL) {
            store->semantic_failures++;
            store->records.loaded = false;
        }
        return false;
    }
    return true;
}

bool openref_boot_state_store_factory_initialize(
    openref_boot_state_store_t *store,
    const openref_boot_state_t *initial_state)
{
    if (store == NULL || initial_state == NULL || !store->initialized ||
        store->records.loaded || !openref_boot_policy_state_valid(initial_state) ||
        initial_state->pending_slot != OPENREF_BOOT_NO_SLOT ||
        initial_state->pending_attempts != 0u) {
        return false;
    }
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];
    encode(initial_state, payload);
    return openref_config_store_save(&store->records, payload);
}

bool openref_boot_state_store_save(
    openref_boot_state_store_t *store,
    const openref_boot_state_t *state)
{
    if (store == NULL || state == NULL || !store->initialized ||
        !store->records.loaded || !openref_boot_policy_state_valid(state) ||
        (state->pending_slot == OPENREF_BOOT_NO_SLOT &&
         state->pending_attempts != 0u) ||
        state->pending_slot == state->confirmed_slot) {
        if (store != NULL) {
            store->semantic_failures++;
        }
        return false;
    }
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];
    encode(state, payload);
    return openref_config_store_save(&store->records, payload);
}
