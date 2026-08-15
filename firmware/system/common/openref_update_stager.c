#include "openref_update_stager.h"

#include <stddef.h>
#include <string.h>

static bool fail(openref_update_stager_t *stager)
{
    if (stager != NULL) {
        stager->failure_count++;
        stager->active = false;
        stager->failed_latched = true;
        stager->storage.invalidate(stager->storage.context, stager->candidate_slot);
    }
    return false;
}

bool openref_update_stager_init(
    openref_update_stager_t *stager,
    const openref_update_platform_t *platform,
    openref_update_crypto_t crypto,
    openref_update_storage_backend_t storage,
    const openref_boot_state_t *boot_state,
    const openref_boot_slot_t slots[2])
{
    if (stager == NULL || platform == NULL || boot_state == NULL || slots == NULL ||
        storage.erase == NULL || storage.write == NULL || storage.read == NULL ||
        storage.authenticate == NULL || storage.invalidate == NULL ||
        storage.persist_boot_state == NULL ||
        !openref_boot_policy_state_valid(boot_state) ||
        !slots[boot_state->confirmed_slot].present ||
        !slots[boot_state->confirmed_slot].authenticated) {
        return false;
    }
    memset(stager, 0, sizeof(*stager));
    stager->storage = storage;
    stager->boot_state = *boot_state;
    memcpy(stager->slots, slots, sizeof(stager->slots));
    stager->candidate_slot = (uint8_t)(boot_state->confirmed_slot ^ 1u);
    if (!openref_update_verifier_init(&stager->verifier, platform, crypto)) {
        return false;
    }
    stager->initialized = true;
    return true;
}

bool openref_update_stager_begin(
    openref_update_stager_t *stager,
    const uint8_t manifest_wire[OPENREF_UPDATE_MANIFEST_BYTES])
{
    if (stager == NULL || !stager->initialized || stager->active ||
        stager->complete || stager->failed_latched ||
        !openref_update_verifier_begin(&stager->verifier, manifest_wire)) {
        return false;
    }
    if (!stager->storage.erase(stager->storage.context, stager->candidate_slot,
                               stager->verifier.manifest.image_size)) {
        return fail(stager);
    }
    stager->written_bytes = 0u;
    stager->active = true;
    return true;
}

bool openref_update_stager_write(
    openref_update_stager_t *stager,
    const uint8_t *data,
    uint32_t length)
{
    uint8_t readback[OPENREF_UPDATE_STAGER_MAX_CHUNK_BYTES];
    if (stager == NULL || !stager->active || data == NULL || length == 0u ||
        length > sizeof(readback) ||
        !openref_update_verifier_write(&stager->verifier, data, length) ||
        !stager->storage.write(stager->storage.context, stager->candidate_slot,
                               stager->written_bytes, data, length) ||
        !stager->storage.read(stager->storage.context, stager->candidate_slot,
                              stager->written_bytes, readback, length)) {
        return fail(stager);
    }
    uint8_t difference = 0u;
    for (uint32_t index = 0u; index < length; index++) {
        difference |= (uint8_t)(data[index] ^ readback[index]);
    }
    if (difference != 0u) {
        return fail(stager);
    }
    stager->written_bytes += length;
    return true;
}

bool openref_update_stager_finish(openref_update_stager_t *stager)
{
    if (stager == NULL || !stager->active ||
        !openref_update_verifier_finish(&stager->verifier) ||
        !stager->storage.authenticate(
            stager->storage.context, stager->candidate_slot,
            stager->verifier.manifest.image_version,
            stager->verifier.manifest.digest)) {
        return fail(stager);
    }
    openref_boot_slot_t candidate = {
        .present = true,
        .authenticated = true,
        .version = stager->verifier.manifest.image_version,
    };
    openref_boot_slot_t staged_slots[2];
    memcpy(staged_slots, stager->slots, sizeof(staged_slots));
    staged_slots[stager->candidate_slot] = candidate;
    openref_boot_state_t staged_state = stager->boot_state;
    if (!openref_boot_policy_stage(&staged_state, stager->candidate_slot, staged_slots) ||
        !stager->storage.persist_boot_state(stager->storage.context, &staged_state)) {
        return fail(stager);
    }
    stager->boot_state = staged_state;
    memcpy(stager->slots, staged_slots, sizeof(stager->slots));
    stager->active = false;
    stager->complete = true;
    return true;
}
