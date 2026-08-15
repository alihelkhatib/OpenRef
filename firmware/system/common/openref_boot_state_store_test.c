#include <assert.h>
#include <string.h>

#include "openref_boot_state_store.h"

typedef struct {
    uint8_t slots[2][OPENREF_CONFIG_SLOT_BYTES];
    bool readable[2];
    bool write_ok;
    bool corrupt_after_write;
} backend_t;

static bool read_slot(void *context, uint8_t slot, uint8_t *record)
{
    backend_t *backend = context;
    if (slot > 1u || !backend->readable[slot]) return false;
    memcpy(record, backend->slots[slot], OPENREF_CONFIG_SLOT_BYTES);
    return true;
}

static bool write_slot(void *context, uint8_t slot, const uint8_t *record)
{
    backend_t *backend = context;
    if (slot > 1u || !backend->write_ok) return false;
    memcpy(backend->slots[slot], record, OPENREF_CONFIG_SLOT_BYTES);
    backend->readable[slot] = true;
    if (backend->corrupt_after_write) backend->slots[slot][16] ^= 1u;
    return true;
}

static openref_boot_state_store_t make_store(backend_t *backend)
{
    openref_boot_state_store_t store;
    openref_config_backend_t callbacks = {read_slot, write_slot, backend};
    assert(openref_boot_state_store_init(&store, callbacks));
    return store;
}

static void test_factory_initialize_load_save_and_reboot(void)
{
    backend_t backend = {.write_ok = true};
    openref_boot_state_store_t store = make_store(&backend);
    openref_boot_state_t initial = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_NO_SLOT, 0u};
    assert(openref_boot_state_store_factory_initialize(&store, &initial));
    assert(!openref_boot_state_store_factory_initialize(&store, &initial));
    openref_boot_state_t pending = initial;
    pending.pending_slot = OPENREF_BOOT_SLOT_B;
    assert(openref_boot_state_store_save(&store, &pending));

    openref_boot_state_store_t rebooted = make_store(&backend);
    openref_boot_state_t loaded;
    assert(openref_boot_state_store_load(&rebooted, &loaded));
    assert(loaded.pending_slot == OPENREF_BOOT_SLOT_B && loaded.minimum_version == 5u);
}

static void test_corrupt_new_generation_falls_back_to_previous(void)
{
    backend_t backend = {.write_ok = true};
    openref_boot_state_store_t store = make_store(&backend);
    openref_boot_state_t initial = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_NO_SLOT, 0u};
    assert(openref_boot_state_store_factory_initialize(&store, &initial));
    backend.corrupt_after_write = true;
    openref_boot_state_t pending = initial;
    pending.pending_slot = OPENREF_BOOT_SLOT_B;
    assert(!openref_boot_state_store_save(&store, &pending));

    openref_boot_state_store_t rebooted = make_store(&backend);
    openref_boot_state_t loaded;
    assert(openref_boot_state_store_load(&rebooted, &loaded));
    assert(loaded.pending_slot == OPENREF_BOOT_NO_SLOT);
}

static void test_semantically_invalid_record_and_save_are_rejected(void)
{
    backend_t backend = {.write_ok = true};
    openref_boot_state_store_t store = make_store(&backend);
    openref_boot_state_t invalid = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_SLOT_A, 0u};
    assert(!openref_boot_state_store_factory_initialize(&store, &invalid));
    openref_boot_state_t initial = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_NO_SLOT, 0u};
    assert(openref_boot_state_store_factory_initialize(&store, &initial));
    invalid = initial;
    invalid.pending_attempts = 1u;
    assert(!openref_boot_state_store_save(&store, &invalid));
}

static void test_runtime_save_requires_successful_load(void)
{
    backend_t backend = {.write_ok = true};
    openref_boot_state_store_t store = make_store(&backend);
    openref_boot_state_t state = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_NO_SLOT, 0u};
    assert(!openref_boot_state_store_save(&store, &state));
}

static void test_generation_exhaustion_fails_without_wrap(void)
{
    backend_t backend = {.write_ok = true};
    openref_boot_state_store_t store = make_store(&backend);
    openref_boot_state_t state = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_NO_SLOT, 0u};
    assert(openref_boot_state_store_factory_initialize(&store, &state));
    store.records.generation = UINT32_MAX;
    assert(!openref_boot_state_store_save(&store, &state));
    assert(store.records.generation == UINT32_MAX);
}

int main(void)
{
    test_factory_initialize_load_save_and_reboot();
    test_corrupt_new_generation_falls_back_to_previous();
    test_semantically_invalid_record_and_save_are_rejected();
    test_runtime_save_requires_successful_load();
    test_generation_exhaustion_fails_without_wrap();
    return 0;
}
