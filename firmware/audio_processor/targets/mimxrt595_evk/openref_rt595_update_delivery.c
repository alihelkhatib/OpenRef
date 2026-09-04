#include "openref_rt595_update_delivery.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static bool region(uint32_t base, uint32_t size)
{
    return size != 0u && base <= UINT32_MAX - size;
}

static bool overlaps(uint32_t a, uint32_t an, uint32_t b, uint32_t bn)
{
    return a < b + bn && b < a + an;
}

static void abort_active(openref_rt595_update_delivery_t *d)
{
    if (d->active && d->target_slot < OPENREF_RT595_UPDATE_SLOT_COUNT) {
        openref_rt595_update_staging_abort(d->slot[d->target_slot]);
    }
    d->verifier.active = false;
    d->verifier.verified = false;
    d->active = false;
    d->session_id = 0u;
    d->next_sequence = 0u;
    d->accepted_bytes = 0u;
}

static openref_rt595_update_delivery_result_t protocol_failure(
    openref_rt595_update_delivery_t *d)
{
    if (d != NULL && d->rejected_messages != UINT32_MAX) {
        ++d->rejected_messages;
    }
    if (d != NULL) {
        abort_active(d);
    }
    return OPENREF_RT595_UPDATE_DELIVERY_PROTOCOL_FAILED;
}

static bool timed_out(const openref_rt595_update_delivery_t *d, uint32_t now)
{
    return d->active && (uint32_t)(now - d->last_activity_us) > d->timeout_us;
}

bool openref_rt595_update_delivery_init(openref_rt595_update_delivery_t *d,
    openref_rt595_update_staging_t *a, openref_rt595_update_staging_t *b,
    uint8_t running, uint32_t executing_base, uint32_t executing_capacity,
    uint32_t timeout, const openref_update_platform_t *platform,
    openref_update_crypto_t crypto, openref_rt595_update_activate_fn activate,
    void *activate_context)
{
    if (d == NULL || a == NULL || b == NULL || a == b || running >= 2u ||
        activate == NULL || timeout == 0u || timeout >= 0x80000000u ||
        !region(executing_base, executing_capacity) ||
        !region(a->manifest_base, a->sector_bytes) || !region(a->base, a->capacity) ||
        !region(b->manifest_base, b->sector_bytes) || !region(b->base, b->capacity) ||
        overlaps(a->manifest_base, a->sector_bytes, b->manifest_base, b->sector_bytes) ||
        overlaps(a->manifest_base, a->sector_bytes, b->base, b->capacity) ||
        overlaps(b->manifest_base, b->sector_bytes, a->base, a->capacity) ||
        overlaps(a->base, a->capacity, b->base, b->capacity) ||
        !openref_update_verifier_init(&d->verifier, platform, crypto)) {
        return false;
    }
    openref_rt595_update_staging_t *inactive = running == 0u ? b : a;
    if (overlaps(inactive->manifest_base, inactive->sector_bytes,
                 executing_base, executing_capacity) ||
        overlaps(inactive->base, inactive->capacity,
                 executing_base, executing_capacity)) {
        return false;
    }
    openref_update_verifier_t verifier = d->verifier;
    memset(d, 0, sizeof(*d));
    d->slot[0] = a;
    d->slot[1] = b;
    d->platform = *platform;
    d->crypto = crypto;
    d->verifier = verifier;
    d->activate = activate;
    d->activate_context = activate_context;
    d->running_slot = running;
    d->executing_image_base = executing_base;
    d->executing_image_capacity = executing_capacity;
    d->timeout_us = timeout;
    return true;
}

openref_rt595_update_delivery_result_t openref_rt595_update_delivery_begin(
    openref_rt595_update_delivery_t *d, uint32_t session, uint8_t target,
    const uint8_t manifest[OPENREF_UPDATE_MANIFEST_BYTES], uint32_t now)
{
    if (d == NULL || manifest == NULL || d->active || session == 0u ||
        session <= d->highest_session_id || target >= 2u ||
        target == d->running_slot) {
        if (d != NULL && d->rejected_messages != UINT32_MAX) ++d->rejected_messages;
        return OPENREF_RT595_UPDATE_DELIVERY_REJECTED;
    }
    /* Authenticate and apply rollback/size policy before any flash erase. */
    if (!openref_update_verifier_begin(&d->verifier, manifest)) {
        ++d->rejected_messages;
        return OPENREF_RT595_UPDATE_DELIVERY_AUTH_FAILED;
    }
    d->highest_session_id = session; /* Reserve even failed/aborted sessions. */
    d->session_id = session;
    d->target_slot = target;
    d->last_activity_us = now;
    if (!openref_rt595_update_staging_start(d->slot[target], &d->verifier)) {
        d->verifier.active = false;
        d->verifier.verified = false;
        d->session_id = 0u;
        return OPENREF_RT595_UPDATE_DELIVERY_STORAGE_FAILED;
    }
    d->active = true;
    d->completed = false;
    d->next_sequence = 0u;
    d->accepted_bytes = 0u;
    return OPENREF_RT595_UPDATE_DELIVERY_OK;
}

openref_rt595_update_delivery_result_t openref_rt595_update_delivery_chunk(
    openref_rt595_update_delivery_t *d, uint32_t session, uint32_t sequence,
    uint32_t offset, const uint8_t *data, uint16_t length, uint32_t now)
{
    if (d == NULL) return OPENREF_RT595_UPDATE_DELIVERY_REJECTED;
    if (timed_out(d, now)) {
        abort_active(d);
        return OPENREF_RT595_UPDATE_DELIVERY_TIMED_OUT;
    }
    if (!d->active || session != d->session_id || sequence != d->next_sequence ||
        offset != d->accepted_bytes || data == NULL || length == 0u ||
        length > OPENREF_RT595_UPDATE_MAX_CHUNK_BYTES ||
        d->accepted_bytes > d->verifier.manifest.image_size ||
        length > d->verifier.manifest.image_size - d->accepted_bytes) {
        return protocol_failure(d);
    }
    if (!openref_rt595_update_staging_write(d->slot[d->target_slot], data, length)) {
        abort_active(d);
        return OPENREF_RT595_UPDATE_DELIVERY_STORAGE_FAILED;
    }
    d->accepted_bytes += length;
    ++d->next_sequence;
    d->last_activity_us = now;
    return OPENREF_RT595_UPDATE_DELIVERY_OK;
}

openref_rt595_update_delivery_result_t openref_rt595_update_delivery_finish(
    openref_rt595_update_delivery_t *d, uint32_t session, uint32_t sequence,
    uint32_t now)
{
    if (d == NULL) return OPENREF_RT595_UPDATE_DELIVERY_REJECTED;
    if (timed_out(d, now)) {
        abort_active(d);
        return OPENREF_RT595_UPDATE_DELIVERY_TIMED_OUT;
    }
    if (!d->active || session != d->session_id || sequence != d->next_sequence ||
        d->accepted_bytes != d->verifier.manifest.image_size) {
        return protocol_failure(d);
    }
    if (!openref_rt595_update_staging_finish(d->slot[d->target_slot])) {
        abort_active(d);
        return OPENREF_RT595_UPDATE_DELIVERY_AUTH_FAILED;
    }
    /* The candidate becomes boot-eligible only after the authenticated
     * manifest commit is durable.  A failed state update leaves a valid but
     * unselected slot and is therefore fail-safe. */
    if (!d->activate(d->activate_context, d->target_slot,
                     d->verifier.manifest.image_version)) {
        d->active = false;
        d->session_id = 0u;
        return OPENREF_RT595_UPDATE_DELIVERY_STORAGE_FAILED;
    }
    d->active = false;
    d->completed = true;
    d->session_id = 0u;
    return OPENREF_RT595_UPDATE_DELIVERY_OK;
}

bool openref_rt595_update_delivery_poll(openref_rt595_update_delivery_t *d,
    uint32_t now)
{
    if (d == NULL || !timed_out(d, now)) return false;
    abort_active(d);
    return true;
}

void openref_rt595_update_delivery_reset(openref_rt595_update_delivery_t *d)
{
    if (d != NULL) abort_active(d);
}
