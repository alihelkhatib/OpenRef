#include "openref_rt595_boot_coordinator.h"

#include <stddef.h>
#include <string.h>

static openref_boot_decision_t no_decision(void)
{
    openref_boot_decision_t decision = {
        .slot = OPENREF_BOOT_NO_SLOT,
        .kind = OPENREF_BOOT_DECISION_NONE,
        .state_changed = false,
    };
    return decision;
}

bool openref_rt595_boot_coordinator_init(
    openref_rt595_boot_coordinator_t *coordinator,
    openref_rt595_slot_authenticator_t *authenticator,
    openref_rt595_boot_state_store_t *state_store,
    uint8_t maximum_trial_attempts)
{
    if (coordinator == NULL || authenticator == NULL ||
        state_store == NULL || !authenticator->initialized ||
        maximum_trial_attempts == 0u) {
        return false;
    }
    coordinator->authenticator = authenticator;
    coordinator->state_store = state_store;
    coordinator->maximum_trial_attempts = maximum_trial_attempts;
    return true;
}

openref_boot_decision_t openref_rt595_boot_coordinator_select(
    openref_rt595_boot_coordinator_t *coordinator,
    openref_boot_slot_t authenticated_slots[2])
{
    openref_boot_slot_t slots[2];
    uint8_t exhausted_slot = OPENREF_BOOT_NO_SLOT;
    if (authenticated_slots != NULL) {
        memset(authenticated_slots, 0, sizeof(slots));
    }
    if (coordinator == NULL || coordinator->authenticator == NULL ||
        coordinator->state_store == NULL ||
        !coordinator->authenticator->initialized ||
        !coordinator->state_store->loaded) {
        return no_decision();
    }

    if (coordinator->state_store->state.pending_slot <= OPENREF_BOOT_SLOT_B &&
        coordinator->state_store->state.pending_attempts >=
            coordinator->maximum_trial_attempts) {
        exhausted_slot = coordinator->state_store->state.pending_slot;
    }
    memset(slots, 0, sizeof(slots));
    /* The update verifier normally requires a version newer than the running
     * image. At reset, the durable minimum is instead an inclusive rollback
     * floor: the confirmed image at exactly that version must remain bootable. */
    coordinator->authenticator->platform.antirollback_floor =
        coordinator->state_store->state.minimum_version;
    coordinator->authenticator->platform.confirmed_image_version =
        coordinator->state_store->state.minimum_version == 0u
            ? 0u
            : coordinator->state_store->state.minimum_version - 1u;
    (void)openref_rt595_slot_authenticate(
        coordinator->authenticator, OPENREF_BOOT_SLOT_A,
        OPENREF_BOOT_NO_SLOT, &slots[OPENREF_BOOT_SLOT_A]);
    (void)openref_rt595_slot_authenticate(
        coordinator->authenticator, OPENREF_BOOT_SLOT_B,
        OPENREF_BOOT_NO_SLOT, &slots[OPENREF_BOOT_SLOT_B]);

    if (authenticated_slots != NULL) {
        memcpy(authenticated_slots, slots, sizeof(slots));
    }
    if (exhausted_slot <= OPENREF_BOOT_SLOT_B) {
        uint8_t confirmed = coordinator->state_store->state.confirmed_slot;
        if (confirmed > OPENREF_BOOT_SLOT_B || !slots[confirmed].present ||
            !slots[confirmed].authenticated ||
            slots[confirmed].version <
                coordinator->state_store->state.minimum_version) {
            /* Preserve the exhausted pending record as a durable recovery
             * latch.  Clearing it here would allow the same candidate to be
             * staged again on the next reset. */
            return no_decision();
        }
    }
    openref_boot_decision_t decision = openref_rt595_boot_state_select(
        coordinator->state_store, slots,
        coordinator->maximum_trial_attempts);
    /* If the confirmed image is unusable, permit an authenticated alternate
     * exactly through the normal persisted trial path.  Never restage a slot
     * whose attempt budget was just exhausted: that would turn resets into an
     * unbounded retry loop and defeat the durable attempt counter. */
    if (decision.kind == OPENREF_BOOT_DECISION_RECOVERY) {
        if (decision.slot == exhausted_slot ||
            !openref_rt595_boot_state_stage(
                coordinator->state_store, decision.slot, slots)) {
            return no_decision();
        }
        decision = openref_rt595_boot_state_select(
            coordinator->state_store, slots,
            coordinator->maximum_trial_attempts);
    }
    return decision;
}
