#include "openref_boot_policy.h"

#include <stddef.h>

static bool slot_id_valid(uint8_t slot)
{
    return slot == OPENREF_BOOT_SLOT_A || slot == OPENREF_BOOT_SLOT_B;
}

static bool eligible(
    const openref_boot_state_t *state,
    const openref_boot_slot_t *slot)
{
    return slot->present && slot->authenticated &&
        slot->version >= state->minimum_version;
}

bool openref_boot_policy_state_valid(const openref_boot_state_t *state)
{
    return state != NULL && state->record_version == 1u &&
        slot_id_valid(state->confirmed_slot) &&
        (state->pending_slot == OPENREF_BOOT_NO_SLOT ||
         slot_id_valid(state->pending_slot));
}

bool openref_boot_policy_stage(
    openref_boot_state_t *state,
    uint8_t candidate_slot,
    const openref_boot_slot_t slots[2])
{
    if (!openref_boot_policy_state_valid(state) || slots == NULL ||
        !slot_id_valid(candidate_slot) || candidate_slot == state->confirmed_slot ||
        !eligible(state, &slots[candidate_slot])) {
        return false;
    }
    state->pending_slot = candidate_slot;
    state->pending_attempts = 0u;
    return true;
}

openref_boot_decision_t openref_boot_policy_select(
    openref_boot_state_t *state,
    const openref_boot_slot_t slots[2],
    uint8_t maximum_trial_attempts)
{
    openref_boot_decision_t decision = {
        .slot = OPENREF_BOOT_NO_SLOT,
        .kind = OPENREF_BOOT_DECISION_NONE,
    };
    if (!openref_boot_policy_state_valid(state) || slots == NULL ||
        maximum_trial_attempts == 0u) {
        return decision;
    }
    if (slot_id_valid(state->pending_slot) &&
        eligible(state, &slots[state->pending_slot]) &&
        state->pending_attempts < maximum_trial_attempts) {
        state->pending_attempts++;
        decision.slot = state->pending_slot;
        decision.kind = OPENREF_BOOT_DECISION_TRIAL;
        decision.state_changed = true;
        return decision;
    }
    if (state->pending_slot != OPENREF_BOOT_NO_SLOT) {
        state->pending_slot = OPENREF_BOOT_NO_SLOT;
        state->pending_attempts = 0u;
        decision.state_changed = true;
    }
    if (eligible(state, &slots[state->confirmed_slot])) {
        decision.slot = state->confirmed_slot;
        decision.kind = decision.state_changed
            ? OPENREF_BOOT_DECISION_FALLBACK
            : OPENREF_BOOT_DECISION_CONFIRMED;
        return decision;
    }
    uint8_t other = (uint8_t)(state->confirmed_slot ^ 1u);
    if (eligible(state, &slots[other])) {
        decision.slot = other;
        decision.kind = OPENREF_BOOT_DECISION_RECOVERY;
    }
    return decision;
}

bool openref_boot_policy_confirm(
    openref_boot_state_t *state,
    uint8_t running_slot,
    const openref_boot_slot_t slots[2])
{
    if (!openref_boot_policy_state_valid(state) || slots == NULL ||
        !slot_id_valid(running_slot) || !eligible(state, &slots[running_slot]) ||
        (running_slot != state->confirmed_slot &&
         running_slot != state->pending_slot)) {
        return false;
    }
    state->confirmed_slot = running_slot;
    state->pending_slot = OPENREF_BOOT_NO_SLOT;
    state->pending_attempts = 0u;
    if (slots[running_slot].version > state->minimum_version) {
        state->minimum_version = slots[running_slot].version;
    }
    return true;
}
