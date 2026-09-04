#ifndef OPENREF_RT595_UPDATE_DELIVERY_H
#define OPENREF_RT595_UPDATE_DELIVERY_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_rt595_update_staging.h"

#define OPENREF_RT595_UPDATE_SLOT_COUNT 2u
#define OPENREF_RT595_UPDATE_MAX_CHUNK_BYTES 512u

typedef enum {
    OPENREF_RT595_UPDATE_DELIVERY_OK = 0,
    OPENREF_RT595_UPDATE_DELIVERY_REJECTED,
    OPENREF_RT595_UPDATE_DELIVERY_AUTH_FAILED,
    OPENREF_RT595_UPDATE_DELIVERY_STORAGE_FAILED,
    OPENREF_RT595_UPDATE_DELIVERY_PROTOCOL_FAILED,
    OPENREF_RT595_UPDATE_DELIVERY_TIMED_OUT
} openref_rt595_update_delivery_result_t;

typedef bool (*openref_rt595_update_activate_fn)(void *context,
    uint8_t candidate_slot, uint32_t image_version);

typedef struct {
    openref_rt595_update_staging_t *slot[OPENREF_RT595_UPDATE_SLOT_COUNT];
    openref_update_platform_t platform;
    openref_update_crypto_t crypto;
    openref_update_verifier_t verifier;
    openref_rt595_update_activate_fn activate;
    void *activate_context;
    uint32_t executing_image_base;
    uint32_t executing_image_capacity;
    uint32_t timeout_us;
    uint32_t highest_session_id;
    uint32_t session_id;
    uint32_t next_sequence;
    uint32_t accepted_bytes;
    uint32_t last_activity_us;
    uint32_t rejected_messages;
    uint8_t running_slot;
    uint8_t target_slot;
    bool active;
    bool completed;
} openref_rt595_update_delivery_t;

bool openref_rt595_update_delivery_init(openref_rt595_update_delivery_t *delivery,
    openref_rt595_update_staging_t *slot_a,
    openref_rt595_update_staging_t *slot_b,
    uint8_t running_slot,
    uint32_t executing_image_base,
    uint32_t executing_image_capacity,
    uint32_t timeout_us,
    const openref_update_platform_t *platform,
    openref_update_crypto_t crypto,
    openref_rt595_update_activate_fn activate,
    void *activate_context);

openref_rt595_update_delivery_result_t openref_rt595_update_delivery_begin(
    openref_rt595_update_delivery_t *delivery,
    uint32_t session_id,
    uint8_t target_slot,
    const uint8_t manifest[OPENREF_UPDATE_MANIFEST_BYTES],
    uint32_t now_us);

openref_rt595_update_delivery_result_t openref_rt595_update_delivery_chunk(
    openref_rt595_update_delivery_t *delivery,
    uint32_t session_id,
    uint32_t sequence,
    uint32_t offset,
    const uint8_t *data,
    uint16_t length,
    uint32_t now_us);

openref_rt595_update_delivery_result_t openref_rt595_update_delivery_finish(
    openref_rt595_update_delivery_t *delivery,
    uint32_t session_id,
    uint32_t sequence,
    uint32_t now_us);

bool openref_rt595_update_delivery_poll(openref_rt595_update_delivery_t *delivery,
    uint32_t now_us);
void openref_rt595_update_delivery_reset(openref_rt595_update_delivery_t *delivery);

#endif
