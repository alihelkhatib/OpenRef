#ifndef OPENREF_DEVICE_LIFECYCLE_H
#define OPENREF_DEVICE_LIFECYCLE_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_DEVICE_ID_BYTES 16u
#define OPENREF_IDENTITY_FINGERPRINT_BYTES 8u

typedef enum {
    OPENREF_DEVICE_BLANK = 0,
    OPENREF_DEVICE_FACTORY_TEST,
    OPENREF_DEVICE_IDENTITY_INSTALLED,
    OPENREF_DEVICE_PRODUCTION_LOCKED,
    OPENREF_DEVICE_QUARANTINED,
    OPENREF_DEVICE_RETIRED
} openref_device_state_t;

typedef struct {
    openref_device_state_t state;
    uint8_t device_id[OPENREF_DEVICE_ID_BYTES];
    uint8_t identity_fingerprint[OPENREF_IDENTITY_FINGERPRINT_BYTES];
    uint32_t generation;
    uint32_t failure_code;
} openref_device_record_t;

typedef bool (*openref_device_record_store_fn)(
    void *context, const openref_device_record_t *record);
typedef bool (*openref_device_identity_generate_fn)(
    void *context, const uint8_t device_id[OPENREF_DEVICE_ID_BYTES],
    uint8_t fingerprint[OPENREF_IDENTITY_FINGERPRINT_BYTES]);
typedef bool (*openref_device_lock_debug_fn)(void *context);
typedef bool (*openref_device_retire_identity_fn)(void *context);

typedef struct {
    openref_device_record_store_fn store_record;
    openref_device_identity_generate_fn generate_identity;
    openref_device_lock_debug_fn lock_debug;
    openref_device_retire_identity_fn retire_identity;
    void *context;
} openref_device_backend_t;

typedef struct {
    openref_device_backend_t backend;
    openref_device_record_t record;
    uint32_t rejected_transitions;
    uint32_t backend_failures;
} openref_device_lifecycle_t;

bool openref_device_record_valid(const openref_device_record_t *record);

bool openref_device_lifecycle_init(
    openref_device_lifecycle_t *lifecycle,
    openref_device_backend_t backend,
    const openref_device_record_t *persisted_record);

bool openref_device_begin_factory_test(openref_device_lifecycle_t *lifecycle);

bool openref_device_install_identity(
    openref_device_lifecycle_t *lifecycle,
    const uint8_t device_id[OPENREF_DEVICE_ID_BYTES],
    bool hardware_tests_passed,
    bool factory_images_authenticated);

bool openref_device_apply_production_lock(
    openref_device_lifecycle_t *lifecycle,
    bool release_images_authenticated,
    bool authenticated_boot_verified);

bool openref_device_quarantine(
    openref_device_lifecycle_t *lifecycle,
    uint32_t failure_code);

bool openref_device_retire(
    openref_device_lifecycle_t *lifecycle,
    bool retirement_authorized);

#endif
