#include <assert.h>
#include <string.h>

#include "openref_device_record_store.h"

typedef struct {
    uint8_t slots[2][OPENREF_CONFIG_SLOT_BYTES];
    bool readable[2];
    bool write_ok;
    bool corrupt_after_write;
} storage_t;

typedef struct {
    openref_device_record_store_t *store;
} lifecycle_backend_t;

static bool read_slot(void *context, uint8_t slot, uint8_t *record)
{
    storage_t *storage = context;
    if (slot > 1u || !storage->readable[slot]) return false;
    memcpy(record, storage->slots[slot], OPENREF_CONFIG_SLOT_BYTES);
    return true;
}

static bool write_slot(void *context, uint8_t slot, const uint8_t *record)
{
    storage_t *storage = context;
    if (slot > 1u || !storage->write_ok) return false;
    memcpy(storage->slots[slot], record, OPENREF_CONFIG_SLOT_BYTES);
    storage->readable[slot] = true;
    if (storage->corrupt_after_write) storage->slots[slot][20] ^= 1u;
    return true;
}

static openref_device_record_store_t make_store(storage_t *storage)
{
    openref_device_record_store_t store;
    openref_config_backend_t backend = {read_slot, write_slot, storage};
    assert(openref_device_record_store_init(&store, backend));
    return store;
}

static bool generate_identity(void *context, const uint8_t *device_id,
                              uint8_t *fingerprint)
{
    (void)context;
    for (uint8_t i = 0u; i < OPENREF_IDENTITY_FINGERPRINT_BYTES; i++) {
        fingerprint[i] = (uint8_t)(device_id[i] ^ 0x5au);
    }
    return true;
}

static bool accept(void *context)
{
    (void)context;
    return true;
}

static void test_lifecycle_persists_and_recovers_across_reboot(void)
{
    storage_t storage = {.write_ok = true};
    openref_device_record_store_t store = make_store(&storage);
    openref_device_record_t record;
    assert(openref_device_record_store_factory_initialize(&store));

    openref_device_record_store_t rebooted = make_store(&storage);
    assert(openref_device_record_store_load(&rebooted, &record));
    openref_device_backend_t backend = {
        openref_device_record_store_callback, generate_identity, accept, accept,
        &rebooted,
    };
    openref_device_lifecycle_t lifecycle;
    assert(openref_device_lifecycle_init(&lifecycle, backend, &record));
    uint8_t device_id[OPENREF_DEVICE_ID_BYTES];
    memset(device_id, 0x35, sizeof(device_id));
    assert(openref_device_begin_factory_test(&lifecycle));
    assert(openref_device_install_identity(&lifecycle, device_id, true, true));
    assert(openref_device_apply_production_lock(&lifecycle, true, true));

    openref_device_record_store_t final_store = make_store(&storage);
    assert(openref_device_record_store_load(&final_store, &record));
    assert(record.state == OPENREF_DEVICE_PRODUCTION_LOCKED);
    assert(record.generation == 3u);
    assert(memcmp(record.device_id, device_id, sizeof(device_id)) == 0);
}

static void test_corrupt_new_copy_falls_back_to_prior_lifecycle_state(void)
{
    storage_t storage = {.write_ok = true};
    openref_device_record_store_t store = make_store(&storage);
    assert(openref_device_record_store_factory_initialize(&store));
    openref_device_record_t factory = {.state = OPENREF_DEVICE_FACTORY_TEST,
                                       .generation = 1u};
    assert(openref_device_record_store_save(&store, &factory));
    storage.corrupt_after_write = true;
    factory.generation = 2u;
    assert(!openref_device_record_store_save(&store, &factory));

    openref_device_record_store_t rebooted = make_store(&storage);
    openref_device_record_t loaded;
    assert(openref_device_record_store_load(&rebooted, &loaded));
    assert(loaded.state == OPENREF_DEVICE_FACTORY_TEST);
    assert(loaded.generation == 1u);
}

static void test_invalid_records_and_unloaded_runtime_save_fail(void)
{
    storage_t storage = {.write_ok = true};
    openref_device_record_store_t store = make_store(&storage);
    openref_device_record_t invalid = {.state = OPENREF_DEVICE_PRODUCTION_LOCKED,
                                       .generation = 1u};
    assert(!openref_device_record_store_save(&store, &invalid));
    assert(openref_device_record_store_factory_initialize(&store));
    assert(!openref_device_record_store_save(&store, &invalid));
}

int main(void)
{
    test_lifecycle_persists_and_recovers_across_reboot();
    test_corrupt_new_copy_falls_back_to_prior_lifecycle_state();
    test_invalid_records_and_unloaded_runtime_save_fail();
    return 0;
}
