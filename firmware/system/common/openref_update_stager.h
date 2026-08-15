#ifndef OPENREF_UPDATE_STAGER_H
#define OPENREF_UPDATE_STAGER_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_boot_policy.h"
#include "openref_update_verifier.h"

#define OPENREF_UPDATE_STAGER_MAX_CHUNK_BYTES 256u

typedef bool (*openref_update_slot_erase_fn)(void *context, uint8_t slot, uint32_t image_size);
typedef bool (*openref_update_slot_write_fn)(void *context, uint8_t slot, uint32_t offset,
                                             const uint8_t *data, uint32_t length);
typedef bool (*openref_update_slot_read_fn)(void *context, uint8_t slot, uint32_t offset,
                                            uint8_t *data, uint32_t length);
typedef bool (*openref_update_slot_authenticate_fn)(
    void *context, uint8_t slot, uint32_t version,
    const uint8_t digest[OPENREF_UPDATE_DIGEST_BYTES]);
typedef bool (*openref_update_slot_invalidate_fn)(void *context, uint8_t slot);
typedef bool (*openref_update_boot_state_persist_fn)(
    void *context, const openref_boot_state_t *state);

typedef struct {
    openref_update_slot_erase_fn erase;
    openref_update_slot_write_fn write;
    openref_update_slot_read_fn read;
    openref_update_slot_authenticate_fn authenticate;
    openref_update_slot_invalidate_fn invalidate;
    openref_update_boot_state_persist_fn persist_boot_state;
    void *context;
} openref_update_storage_backend_t;

typedef struct {
    openref_update_verifier_t verifier;
    openref_update_storage_backend_t storage;
    openref_boot_state_t boot_state;
    openref_boot_slot_t slots[2];
    uint8_t candidate_slot;
    uint32_t written_bytes;
    uint32_t failure_count;
    bool active;
    bool complete;
    bool failed_latched;
    bool initialized;
} openref_update_stager_t;

bool openref_update_stager_init(
    openref_update_stager_t *stager,
    const openref_update_platform_t *platform,
    openref_update_crypto_t crypto,
    openref_update_storage_backend_t storage,
    const openref_boot_state_t *boot_state,
    const openref_boot_slot_t slots[2]);

bool openref_update_stager_begin(
    openref_update_stager_t *stager,
    const uint8_t manifest_wire[OPENREF_UPDATE_MANIFEST_BYTES]);

bool openref_update_stager_write(
    openref_update_stager_t *stager,
    const uint8_t *data,
    uint32_t length);

bool openref_update_stager_finish(openref_update_stager_t *stager);

#endif
