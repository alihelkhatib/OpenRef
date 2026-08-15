#include <assert.h>
#include <string.h>

#include "openref_device_lifecycle.h"

typedef struct {
    bool store_ok;
    bool identity_ok;
    bool lock_ok;
    bool retire_ok;
    openref_device_record_t stored;
    uint32_t stores;
} backend_state_t;

static bool store_record(void *context, const openref_device_record_t *record)
{
    backend_state_t *state = context;
    state->stores++;
    state->stored = *record;
    return state->store_ok;
}

static bool generate_identity(void *context, const uint8_t *device_id,
                              uint8_t *fingerprint)
{
    backend_state_t *state = context;
    if (!state->identity_ok) {
        return false;
    }
    for (uint8_t i = 0u; i < OPENREF_IDENTITY_FINGERPRINT_BYTES; i++) {
        fingerprint[i] = (uint8_t)(device_id[i] ^ 0xa5u);
    }
    return true;
}

static bool lock_debug(void *context)
{
    return ((backend_state_t *)context)->lock_ok;
}

static bool retire_identity(void *context)
{
    return ((backend_state_t *)context)->retire_ok;
}

static openref_device_lifecycle_t make_lifecycle(backend_state_t *state)
{
    openref_device_backend_t backend = {
        store_record, generate_identity, lock_debug, retire_identity, state,
    };
    openref_device_lifecycle_t lifecycle;
    assert(openref_device_lifecycle_init(&lifecycle, backend, NULL));
    return lifecycle;
}

static void test_ordered_provision_lock_and_retire(void)
{
    backend_state_t state = {
        .store_ok = true, .identity_ok = true, .lock_ok = true,
        .retire_ok = true,
    };
    openref_device_lifecycle_t lifecycle = make_lifecycle(&state);
    uint8_t id[OPENREF_DEVICE_ID_BYTES];
    memset(id, 0x31, sizeof(id));
    assert(openref_device_begin_factory_test(&lifecycle));
    assert(openref_device_install_identity(&lifecycle, id, true, true));
    assert(lifecycle.record.state == OPENREF_DEVICE_IDENTITY_INSTALLED);
    assert(openref_device_apply_production_lock(&lifecycle, true, true));
    assert(lifecycle.record.state == OPENREF_DEVICE_PRODUCTION_LOCKED);
    assert(openref_device_retire(&lifecycle, true));
    assert(lifecycle.record.state == OPENREF_DEVICE_RETIRED);
    for (uint8_t i = 0u; i < OPENREF_IDENTITY_FINGERPRINT_BYTES; i++) {
        assert(lifecycle.record.identity_fingerprint[i] == 0u);
    }
    assert(!openref_device_begin_factory_test(&lifecycle));
}

static void test_evidence_and_backend_failures_quarantine(void)
{
    backend_state_t state = {.store_ok = true, .identity_ok = true};
    openref_device_lifecycle_t lifecycle = make_lifecycle(&state);
    uint8_t id[OPENREF_DEVICE_ID_BYTES];
    memset(id, 1, sizeof(id));
    assert(openref_device_begin_factory_test(&lifecycle));
    assert(!openref_device_install_identity(&lifecycle, id, false, true));
    assert(lifecycle.record.state == OPENREF_DEVICE_FACTORY_TEST);
    state.identity_ok = false;
    assert(!openref_device_install_identity(&lifecycle, id, true, true));
    assert(lifecycle.record.state == OPENREF_DEVICE_QUARANTINED);

    state = (backend_state_t){.store_ok = false, .identity_ok = true};
    lifecycle = make_lifecycle(&state);
    assert(!openref_device_begin_factory_test(&lifecycle));
    assert(lifecycle.record.state == OPENREF_DEVICE_QUARANTINED);
}

static void test_explicit_quarantine_and_corrupt_persisted_state(void)
{
    backend_state_t state = {
        .store_ok = true, .identity_ok = true, .lock_ok = true,
        .retire_ok = true,
    };
    openref_device_lifecycle_t lifecycle = make_lifecycle(&state);
    assert(openref_device_quarantine(&lifecycle, 0x1234u));
    assert(lifecycle.record.state == OPENREF_DEVICE_QUARANTINED);
    assert(lifecycle.record.failure_code == 0x1234u);

    openref_device_record_t corrupt = {
        .state = OPENREF_DEVICE_PRODUCTION_LOCKED, .generation = 2u,
    };
    openref_device_backend_t backend = {
        store_record, generate_identity, lock_debug, retire_identity, &state,
    };
    assert(openref_device_lifecycle_init(&lifecycle, backend, &corrupt));
    assert(lifecycle.record.state == OPENREF_DEVICE_QUARANTINED);
}

int main(void)
{
    test_ordered_provision_lock_and_retire();
    test_evidence_and_backend_failures_quarantine();
    test_explicit_quarantine_and_corrupt_persisted_state();
    return 0;
}
