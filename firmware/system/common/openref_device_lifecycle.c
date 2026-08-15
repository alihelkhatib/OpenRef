#include "openref_device_lifecycle.h"

#include <stddef.h>
#include <string.h>

static bool all_zero(const uint8_t *data, uint8_t length)
{
    uint8_t aggregate = 0u;
    for (uint8_t i = 0u; i < length; i++) {
        aggregate |= data[i];
    }
    return aggregate == 0u;
}

bool openref_device_record_valid(const openref_device_record_t *record)
{
    bool id_zero;
    bool fingerprint_zero;
    if (record == NULL || record->state > OPENREF_DEVICE_RETIRED) {
        return false;
    }
    id_zero = all_zero(record->device_id, OPENREF_DEVICE_ID_BYTES);
    fingerprint_zero = all_zero(
        record->identity_fingerprint, OPENREF_IDENTITY_FINGERPRINT_BYTES);
    if (record->state == OPENREF_DEVICE_BLANK) {
        return record->generation == 0u && id_zero && fingerprint_zero &&
            record->failure_code == 0u;
    }
    if (record->generation == 0u) {
        return false;
    }
    if (record->state == OPENREF_DEVICE_FACTORY_TEST) {
        return id_zero && fingerprint_zero && record->failure_code == 0u;
    }
    if (record->state == OPENREF_DEVICE_IDENTITY_INSTALLED ||
        record->state == OPENREF_DEVICE_PRODUCTION_LOCKED) {
        return !id_zero && !fingerprint_zero && record->failure_code == 0u;
    }
    if (record->state == OPENREF_DEVICE_QUARANTINED) {
        return record->failure_code != 0u;
    }
    return !id_zero && fingerprint_zero;
}

static bool persist(openref_device_lifecycle_t *lifecycle)
{
    lifecycle->record.generation++;
    if (lifecycle->record.generation == 0u ||
        !lifecycle->backend.store_record(lifecycle->backend.context,
                                         &lifecycle->record)) {
        lifecycle->backend_failures++;
        lifecycle->record.state = OPENREF_DEVICE_QUARANTINED;
        return false;
    }
    return true;
}

static bool reject(openref_device_lifecycle_t *lifecycle)
{
    if (lifecycle != NULL) {
        lifecycle->rejected_transitions++;
    }
    return false;
}

bool openref_device_lifecycle_init(openref_device_lifecycle_t *lifecycle,
    openref_device_backend_t backend,
    const openref_device_record_t *persisted_record)
{
    if (lifecycle == NULL || backend.store_record == NULL ||
        backend.generate_identity == NULL || backend.lock_debug == NULL ||
        backend.retire_identity == NULL) {
        return false;
    }
    memset(lifecycle, 0, sizeof(*lifecycle));
    lifecycle->backend = backend;
    if (persisted_record != NULL) {
        lifecycle->record = *persisted_record;
        if (!openref_device_record_valid(persisted_record)) {
            lifecycle->record.state = OPENREF_DEVICE_QUARANTINED;
        }
    }
    return true;
}

bool openref_device_begin_factory_test(openref_device_lifecycle_t *lifecycle)
{
    if (lifecycle == NULL || lifecycle->record.state != OPENREF_DEVICE_BLANK) {
        return reject(lifecycle);
    }
    lifecycle->record.state = OPENREF_DEVICE_FACTORY_TEST;
    return persist(lifecycle);
}

bool openref_device_install_identity(openref_device_lifecycle_t *lifecycle,
    const uint8_t device_id[OPENREF_DEVICE_ID_BYTES], bool hardware_tests_passed,
    bool factory_images_authenticated)
{
    if (lifecycle == NULL || device_id == NULL ||
        lifecycle->record.state != OPENREF_DEVICE_FACTORY_TEST ||
        !hardware_tests_passed || !factory_images_authenticated ||
        all_zero(device_id, OPENREF_DEVICE_ID_BYTES)) {
        return reject(lifecycle);
    }
    uint8_t fingerprint[OPENREF_IDENTITY_FINGERPRINT_BYTES] = {0};
    if (!lifecycle->backend.generate_identity(
            lifecycle->backend.context, device_id, fingerprint) ||
        all_zero(fingerprint, sizeof(fingerprint))) {
        lifecycle->backend_failures++;
        lifecycle->record.state = OPENREF_DEVICE_QUARANTINED;
        return false;
    }
    memcpy(lifecycle->record.device_id, device_id, OPENREF_DEVICE_ID_BYTES);
    memcpy(lifecycle->record.identity_fingerprint, fingerprint,
           OPENREF_IDENTITY_FINGERPRINT_BYTES);
    lifecycle->record.state = OPENREF_DEVICE_IDENTITY_INSTALLED;
    return persist(lifecycle);
}

bool openref_device_apply_production_lock(openref_device_lifecycle_t *lifecycle,
    bool release_images_authenticated, bool authenticated_boot_verified)
{
    if (lifecycle == NULL ||
        lifecycle->record.state != OPENREF_DEVICE_IDENTITY_INSTALLED ||
        !release_images_authenticated || !authenticated_boot_verified) {
        return reject(lifecycle);
    }
    if (!lifecycle->backend.lock_debug(lifecycle->backend.context)) {
        lifecycle->backend_failures++;
        lifecycle->record.state = OPENREF_DEVICE_QUARANTINED;
        return false;
    }
    lifecycle->record.state = OPENREF_DEVICE_PRODUCTION_LOCKED;
    return persist(lifecycle);
}

bool openref_device_quarantine(openref_device_lifecycle_t *lifecycle,
    uint32_t failure_code)
{
    if (lifecycle == NULL || failure_code == 0u ||
        lifecycle->record.state == OPENREF_DEVICE_RETIRED) {
        return reject(lifecycle);
    }
    lifecycle->record.failure_code = failure_code;
    lifecycle->record.state = OPENREF_DEVICE_QUARANTINED;
    return persist(lifecycle);
}

bool openref_device_retire(openref_device_lifecycle_t *lifecycle,
    bool retirement_authorized)
{
    if (lifecycle == NULL ||
        lifecycle->record.state != OPENREF_DEVICE_PRODUCTION_LOCKED ||
        !retirement_authorized) {
        return reject(lifecycle);
    }
    bool erased = lifecycle->backend.retire_identity(lifecycle->backend.context);
    memset(lifecycle->record.identity_fingerprint, 0,
           sizeof(lifecycle->record.identity_fingerprint));
    lifecycle->record.state = OPENREF_DEVICE_RETIRED;
    if (!erased) {
        lifecycle->backend_failures++;
    }
    bool stored = persist(lifecycle);
    lifecycle->record.state = OPENREF_DEVICE_RETIRED;
    return erased && stored;
}
