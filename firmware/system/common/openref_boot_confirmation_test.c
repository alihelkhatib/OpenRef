#include <assert.h>

#include "openref_boot_confirmation.h"

typedef struct { bool persist_ok; uint32_t writes; } backend_t;

static bool persist(void *context, const openref_boot_state_t *state)
{
    backend_t *backend = context;
    backend->writes++;
    return backend->persist_ok && state->confirmed_slot == OPENREF_BOOT_SLOT_B &&
        state->pending_slot == OPENREF_BOOT_NO_SLOT && state->minimum_version == 7u;
}

static openref_boot_confirmation_t make_confirmation(backend_t *backend)
{
    openref_boot_state_t state = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_SLOT_B, 1u};
    openref_boot_slot_t slots[2] = {{true, true, 6u}, {true, true, 7u}};
    openref_boot_confirmation_backend_t hooks = {persist, backend};
    openref_boot_confirmation_t confirmation;
    assert(openref_boot_confirmation_init(&confirmation, &state, slots,
                                           OPENREF_BOOT_SLOT_B, 1000u, hooks, 0u));
    return confirmation;
}

static openref_boot_confirmation_inputs_t healthy(void)
{
    openref_boot_confirmation_inputs_t inputs = {true, true, true, true, true, true};
    return inputs;
}

static void test_continuous_soak_confirms_and_advances_floor(void)
{
    backend_t backend = {true, 0u};
    openref_boot_confirmation_t confirmation = make_confirmation(&backend);
    openref_boot_confirmation_inputs_t inputs = healthy();
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 10u));
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 1009u));
    assert(openref_boot_confirmation_tick(&confirmation, &inputs, 1010u));
    assert(confirmation.confirmed && backend.writes == 1u);
    assert(confirmation.boot_state.minimum_version == 7u);
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 2000u));
}

static void test_health_interruption_restarts_entire_soak(void)
{
    backend_t backend = {true, 0u};
    openref_boot_confirmation_t confirmation = make_confirmation(&backend);
    openref_boot_confirmation_inputs_t inputs = healthy();
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 0u));
    inputs.peer_ok = false;
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 900u));
    inputs.peer_ok = true;
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 901u));
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 1900u));
    assert(openref_boot_confirmation_tick(&confirmation, &inputs, 1901u));
    assert(confirmation.interrupted_soaks == 1u);
}

static void test_clock_rollback_restarts_soak(void)
{
    backend_t backend = {true, 0u};
    openref_boot_confirmation_t confirmation = make_confirmation(&backend);
    openref_boot_confirmation_inputs_t inputs = healthy();
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 500u));
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 400u));
    assert(confirmation.clock_faults == 1u && !confirmation.healthy_period_active);
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 401u));
    assert(openref_boot_confirmation_tick(&confirmation, &inputs, 1401u));
}

static void test_persistence_failure_latches_without_advancing_state(void)
{
    backend_t backend = {false, 0u};
    openref_boot_confirmation_t confirmation = make_confirmation(&backend);
    openref_boot_confirmation_inputs_t inputs = healthy();
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 0u));
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 1000u));
    assert(confirmation.persistence_fault_latched && backend.writes == 1u);
    assert(confirmation.boot_state.confirmed_slot == OPENREF_BOOT_SLOT_A);
    backend.persist_ok = true;
    assert(!openref_boot_confirmation_tick(&confirmation, &inputs, 2000u));
    assert(backend.writes == 1u);
}

static void test_wrong_or_unauthenticated_slot_cannot_initialize(void)
{
    backend_t backend = {true, 0u};
    openref_boot_state_t state = {1u, 5u, OPENREF_BOOT_SLOT_A, OPENREF_BOOT_SLOT_B, 0u};
    openref_boot_slot_t slots[2] = {{true, true, 6u}, {true, false, 7u}};
    openref_boot_confirmation_backend_t hooks = {persist, &backend};
    openref_boot_confirmation_t confirmation;
    assert(!openref_boot_confirmation_init(&confirmation, &state, slots,
                                            OPENREF_BOOT_SLOT_A, 1000u, hooks, 0u));
    assert(!openref_boot_confirmation_init(&confirmation, &state, slots,
                                            OPENREF_BOOT_SLOT_B, 1000u, hooks, 0u));
}

int main(void)
{
    test_continuous_soak_confirms_and_advances_floor();
    test_health_interruption_restarts_entire_soak();
    test_clock_rollback_restarts_soak();
    test_persistence_failure_latches_without_advancing_state();
    test_wrong_or_unauthenticated_slot_cannot_initialize();
    return 0;
}
