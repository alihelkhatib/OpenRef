#include "openref_rt595_bootstrap.h"

#include <stddef.h>

static bool fail(openref_rt595_bootstrap_t *bootstrap,
    openref_rt595_bootstrap_recovery_reason_t reason)
{
    if (bootstrap != NULL) {
        bootstrap->last_recovery_reason = reason;
        if (bootstrap->status != NULL) bootstrap->status(bootstrap->context, reason);
    }
    if (bootstrap != NULL && bootstrap->recovery != NULL) {
        bootstrap->recovery(bootstrap->context);
    }
    return false;
}

bool openref_rt595_bootstrap_handoff(openref_rt595_bootstrap_t *bootstrap,
    const openref_boot_decision_t *decision, const openref_boot_slot_t slots[2])
{
    openref_rt595_boot_handoff_layout_t layout;
    openref_rt595_boot_handoff_plan_t plan;
    uint8_t slot;

    if (bootstrap == NULL || decision == NULL || slots == NULL ||
        bootstrap->prepare == NULL || bootstrap->transfer == NULL ||
        bootstrap->recovery == NULL || bootstrap->ram_size == 0u) {
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_CONFIGURATION);
    }
    slot = decision->slot;
    if (decision->kind == OPENREF_BOOT_DECISION_NONE ||
        decision->kind == OPENREF_BOOT_DECISION_RECOVERY || slot > OPENREF_BOOT_SLOT_B ||
        !slots[slot].present || !slots[slot].authenticated ||
        bootstrap->authenticated_image_size[slot] < OPENREF_RT595_BOOT_VECTOR_BYTES ||
        bootstrap->authenticated_image_size[slot] > bootstrap->image_capacity[slot]) {
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_POLICY);
    }
    layout = (openref_rt595_boot_handoff_layout_t){
        .authenticated = true,
        .image_base = bootstrap->image_base[slot],
        .image_size = bootstrap->authenticated_image_size[slot],
        .ram_base = bootstrap->ram_base,
        .ram_size = bootstrap->ram_size,
        .vtor_alignment = bootstrap->vtor_alignment,
    };
    if (!bootstrap->prepare(bootstrap->context, &layout, &plan)) {
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_VECTOR);
    }
    bootstrap->transfer(bootstrap->context, &plan);
    return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_TRANSFER_RETURNED);
}

bool openref_rt595_bootstrap_run(openref_rt595_bootstrap_t *bootstrap)
{
    openref_boot_slot_t slots[2];
    openref_boot_decision_t decision;
    uint32_t read_failures_before;
    if (bootstrap == NULL || bootstrap->coordinator == NULL)
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_CONFIGURATION);
    if (bootstrap->coordinator->state_store == NULL)
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_CONFIGURATION);
    if (!bootstrap->coordinator->state_store->loaded)
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_DURABLE_STATE);
    read_failures_before = bootstrap->coordinator->authenticator == NULL ? 0u :
        bootstrap->coordinator->authenticator->read_failures;
    decision = openref_rt595_boot_coordinator_select(bootstrap->coordinator, slots);
    if (bootstrap->coordinator->authenticator != NULL) {
        bootstrap->authenticated_image_size[0] =
            bootstrap->coordinator->authenticator->authenticated_image_size[0];
        bootstrap->authenticated_image_size[1] =
            bootstrap->coordinator->authenticator->authenticated_image_size[1];
    } else {
        bootstrap->authenticated_image_size[0] = 0u;
        bootstrap->authenticated_image_size[1] = 0u;
    }
    if (decision.kind == OPENREF_BOOT_DECISION_NONE) {
        if (bootstrap->coordinator->authenticator != NULL &&
            bootstrap->coordinator->authenticator->read_failures != read_failures_before)
            return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_FLASH_READ);
        if (!slots[0].authenticated && !slots[1].authenticated)
            return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_NO_AUTHENTICATED_IMAGE);
        return fail(bootstrap, OPENREF_RT595_BOOTSTRAP_RECOVERY_POLICY);
    }
    return openref_rt595_bootstrap_handoff(bootstrap, &decision, slots);
}
