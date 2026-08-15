#include <assert.h>
#include <string.h>

#include "openref_update_stager.h"

typedef struct {
    uint8_t flash[2][1024];
    uint8_t sum;
    uint32_t invalidates;
    uint32_t persists;
    bool corrupt_read;
    bool write_ok;
    bool authenticate_ok;
    bool persist_ok;
} fake_target_t;

static bool signature(void *context, const uint8_t *data,
                      const uint8_t *key, const uint8_t *signature_data)
{
    (void)context;
    return data[0] == 0x4fu && key[0] == 0x33u && signature_data[0] == 0x5au;
}
static bool hash_begin(void *context) { ((fake_target_t *)context)->sum = 0u; return true; }
static bool hash_update(void *context, const uint8_t *data, uint32_t length)
{
    for (uint32_t index = 0u; index < length; index++) {
        ((fake_target_t *)context)->sum += data[index];
    }
    return true;
}
static bool hash_finish(void *context, uint8_t *digest)
{
    for (uint8_t index = 0u; index < 32u; index++) {
        digest[index] = (uint8_t)(((fake_target_t *)context)->sum + index);
    }
    return true;
}
static bool erase(void *context, uint8_t slot, uint32_t size)
{
    fake_target_t *target = context;
    if (size > sizeof(target->flash[slot])) return false;
    memset(target->flash[slot], 0xff, size);
    return true;
}
static bool write_slot(void *context, uint8_t slot, uint32_t offset,
                       const uint8_t *data, uint32_t length)
{
    fake_target_t *target = context;
    if (!target->write_ok || offset + length > sizeof(target->flash[slot])) return false;
    memcpy(&target->flash[slot][offset], data, length);
    return true;
}
static bool read_slot(void *context, uint8_t slot, uint32_t offset,
                      uint8_t *data, uint32_t length)
{
    fake_target_t *target = context;
    memcpy(data, &target->flash[slot][offset], length);
    if (target->corrupt_read && length != 0u) data[0] ^= 1u;
    return true;
}
static bool authenticate(void *context, uint8_t slot, uint32_t version,
                         const uint8_t *digest)
{
    (void)slot;
    return ((fake_target_t *)context)->authenticate_ok && version == 7u && digest[0] == 15u;
}
static bool invalidate(void *context, uint8_t slot)
{
    fake_target_t *target = context;
    target->invalidates++;
    memset(target->flash[slot], 0, sizeof(target->flash[slot]));
    return true;
}
static bool persist(void *context, const openref_boot_state_t *state)
{
    fake_target_t *target = context;
    target->persists++;
    return target->persist_ok && state->pending_slot == OPENREF_BOOT_SLOT_B;
}
static void put_u32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value; data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16); data[3] = (uint8_t)(value >> 24);
}
static void manifest(uint8_t *wire)
{
    memset(wire, 0, 144u);
    wire[0] = 0x4fu; wire[1] = 0x52u; wire[2] = 0x55u; wire[3] = 0x50u;
    wire[4] = 1u; wire[5] = OPENREF_UPDATE_TARGET_RADIO;
    put_u32(&wire[8], 0x12345678u); put_u32(&wire[12], 7u);
    put_u32(&wire[16], 2u); put_u32(&wire[20], 5u);
    for (uint8_t index = 0u; index < 32u; index++) wire[24u + index] = (uint8_t)(15u + index);
    memset(&wire[56], 0x22, 16u); memset(&wire[72], 0x33, 8u); wire[80] = 0x5au;
}
static openref_update_stager_t make_stager(fake_target_t *target)
{
    openref_update_platform_t platform = {OPENREF_UPDATE_TARGET_RADIO, 0x12345678u, 3u, 5u, 6u, 1024u};
    openref_update_crypto_t crypto = {signature, hash_begin, hash_update, hash_finish, target};
    openref_update_storage_backend_t storage = {
        erase, write_slot, read_slot, authenticate, invalidate, persist, target,
    };
    openref_boot_state_t state = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_NO_SLOT, 0u};
    openref_boot_slot_t slots[2] = {{true, true, 6u}, {false, false, 0u}};
    openref_update_stager_t stager;
    assert(openref_update_stager_init(&stager, &platform, crypto, storage, &state, slots));
    return stager;
}

static void test_success_stages_only_inactive_slot(void)
{
    fake_target_t target = {.write_ok = true, .authenticate_ok = true, .persist_ok = true};
    openref_update_stager_t stager = make_stager(&target);
    uint8_t wire[144], image[5] = {1u, 2u, 3u, 4u, 5u}; manifest(wire);
    assert(openref_update_stager_begin(&stager, wire));
    assert(stager.candidate_slot == OPENREF_BOOT_SLOT_B);
    assert(openref_update_stager_write(&stager, image, sizeof(image)));
    assert(openref_update_stager_finish(&stager));
    assert(stager.complete && stager.boot_state.pending_slot == OPENREF_BOOT_SLOT_B);
    assert(target.persists == 1u && target.invalidates == 0u);
}

static void test_readback_corruption_invalidates_and_latches(void)
{
    fake_target_t target = {.write_ok = true, .authenticate_ok = true, .persist_ok = true, .corrupt_read = true};
    openref_update_stager_t stager = make_stager(&target);
    uint8_t wire[144], image[5] = {1u, 2u, 3u, 4u, 5u}; manifest(wire);
    assert(openref_update_stager_begin(&stager, wire));
    assert(!openref_update_stager_write(&stager, image, sizeof(image)));
    assert(stager.failed_latched && target.invalidates == 1u);
    target.corrupt_read = false;
    assert(!openref_update_stager_begin(&stager, wire));
}

static void test_authentication_and_state_persistence_fail_closed(void)
{
    uint8_t wire[144], image[5] = {1u, 2u, 3u, 4u, 5u}; manifest(wire);
    fake_target_t target = {.write_ok = true, .authenticate_ok = false, .persist_ok = true};
    openref_update_stager_t stager = make_stager(&target);
    assert(openref_update_stager_begin(&stager, wire));
    assert(openref_update_stager_write(&stager, image, sizeof(image)));
    assert(!openref_update_stager_finish(&stager));
    assert(target.invalidates == 1u && stager.boot_state.pending_slot == OPENREF_BOOT_NO_SLOT);

    target = (fake_target_t){.write_ok = true, .authenticate_ok = true, .persist_ok = false};
    stager = make_stager(&target);
    assert(openref_update_stager_begin(&stager, wire));
    assert(openref_update_stager_write(&stager, image, sizeof(image)));
    assert(!openref_update_stager_finish(&stager));
    assert(target.persists == 1u && target.invalidates == 1u);
    assert(stager.boot_state.pending_slot == OPENREF_BOOT_NO_SLOT);
}

static void test_truncated_and_oversized_chunks_fail_closed(void)
{
    fake_target_t target = {.write_ok = true, .authenticate_ok = true, .persist_ok = true};
    openref_update_stager_t stager = make_stager(&target);
    uint8_t wire[144], image[300] = {0}; manifest(wire);
    assert(openref_update_stager_begin(&stager, wire));
    assert(!openref_update_stager_write(&stager, image, sizeof(image)));
    assert(target.invalidates == 1u);
}

int main(void)
{
    test_success_stages_only_inactive_slot();
    test_readback_corruption_invalidates_and_latches();
    test_authentication_and_state_persistence_fail_closed();
    test_truncated_and_oversized_chunks_fail_closed();
    return 0;
}
