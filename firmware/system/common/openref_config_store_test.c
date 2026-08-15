#include <assert.h>
#include <string.h>

#include "openref_config_store.h"

typedef struct {
    uint8_t slots[2][OPENREF_CONFIG_SLOT_BYTES];
    bool readable[2];
    bool write_ok;
    bool corrupt_after_write;
} memory_backend_t;

static bool read_slot(void *context, uint8_t slot, uint8_t *record)
{
    memory_backend_t *memory = context;
    if (slot > 1u || !memory->readable[slot]) {
        return false;
    }
    memcpy(record, memory->slots[slot], OPENREF_CONFIG_SLOT_BYTES);
    return true;
}

static bool write_slot(void *context, uint8_t slot, const uint8_t *record)
{
    memory_backend_t *memory = context;
    if (!memory->write_ok || slot > 1u) {
        return false;
    }
    memcpy(memory->slots[slot], record, OPENREF_CONFIG_SLOT_BYTES);
    memory->readable[slot] = true;
    if (memory->corrupt_after_write) {
        memory->slots[slot][20] ^= 1u;
    }
    return true;
}

static openref_config_store_t make_store(memory_backend_t *memory, uint16_t version)
{
    openref_config_store_t store;
    openref_config_backend_t backend = {read_slot, write_slot, memory};
    assert(openref_config_store_init(&store, backend, version, 8u));
    return store;
}

static void test_dual_slot_save_load_and_fallback(void)
{
    memory_backend_t memory = {.write_ok = true};
    openref_config_store_t store = make_store(&memory, 3u);
    uint8_t first[OPENREF_CONFIG_MAX_PAYLOAD_BYTES] = {1u, 2u, 3u};
    uint8_t second[OPENREF_CONFIG_MAX_PAYLOAD_BYTES] = {4u, 5u, 6u};
    assert(openref_config_store_save(&store, first));
    assert(store.active_slot == 0u && store.generation == 1u);
    assert(openref_config_store_save(&store, second));
    assert(store.active_slot == 1u && store.generation == 2u);

    openref_config_store_t rebooted = make_store(&memory, 3u);
    uint8_t loaded[OPENREF_CONFIG_MAX_PAYLOAD_BYTES] = {0};
    assert(openref_config_store_load(&rebooted, loaded));
    assert(loaded[0] == 4u && rebooted.active_slot == 1u);
    memory.slots[1][20] ^= 1u;
    rebooted = make_store(&memory, 3u);
    assert(openref_config_store_load(&rebooted, loaded));
    assert(loaded[0] == 1u && rebooted.active_slot == 0u);
}

static void test_version_mismatch_and_verified_write(void)
{
    memory_backend_t memory = {.write_ok = true};
    openref_config_store_t version_one = make_store(&memory, 1u);
    uint8_t payload[OPENREF_CONFIG_MAX_PAYLOAD_BYTES] = {9u};
    assert(openref_config_store_save(&version_one, payload));
    openref_config_store_t version_two = make_store(&memory, 2u);
    assert(!openref_config_store_load(&version_two, payload));
    assert(version_two.load_failures == 1u);

    memory.corrupt_after_write = true;
    assert(!openref_config_store_save(&version_two, payload));
    assert(!version_two.loaded);
    assert(version_two.write_failures == 1u);
}

int main(void)
{
    test_dual_slot_save_load_and_fallback();
    test_version_mismatch_and_verified_write();
    return 0;
}
