#include <assert.h>
#include <stdbool.h>

#include "openref_boot_policy.h"

int main(void)
{
    openref_boot_slot_t slots[2] = {
        {.present = true, .authenticated = true, .version = 1u},
        {.present = true, .authenticated = true, .version = 2u},
    };
    openref_boot_state_t state = {
        .record_version = 1u,
        .minimum_version = 1u,
        .confirmed_slot = OPENREF_BOOT_SLOT_A,
        .pending_slot = OPENREF_BOOT_NO_SLOT,
    };
    assert(openref_boot_policy_stage(&state, OPENREF_BOOT_SLOT_B, slots));
    for (uint8_t attempt = 1u; attempt <= 3u; attempt++) {
        openref_boot_decision_t decision =
            openref_boot_policy_select(&state, slots, 3u);
        assert(decision.slot == OPENREF_BOOT_SLOT_B);
        assert(decision.kind == OPENREF_BOOT_DECISION_TRIAL);
        assert(state.pending_attempts == attempt);
    }
    openref_boot_decision_t decision = openref_boot_policy_select(&state, slots, 3u);
    assert(decision.slot == OPENREF_BOOT_SLOT_A);
    assert(decision.kind == OPENREF_BOOT_DECISION_FALLBACK);
    assert(state.pending_slot == OPENREF_BOOT_NO_SLOT);

    assert(openref_boot_policy_stage(&state, OPENREF_BOOT_SLOT_B, slots));
    decision = openref_boot_policy_select(&state, slots, 3u);
    assert(decision.slot == OPENREF_BOOT_SLOT_B);
    assert(openref_boot_policy_confirm(&state, OPENREF_BOOT_SLOT_B, slots));
    assert(state.minimum_version == 2u);
    assert(state.confirmed_slot == OPENREF_BOOT_SLOT_B);
    assert(!openref_boot_policy_stage(&state, OPENREF_BOOT_SLOT_A, slots));

    slots[1].authenticated = false;
    decision = openref_boot_policy_select(&state, slots, 3u);
    assert(decision.kind == OPENREF_BOOT_DECISION_NONE);
    slots[0].version = 2u;
    decision = openref_boot_policy_select(&state, slots, 3u);
    assert(decision.slot == OPENREF_BOOT_SLOT_A);
    assert(decision.kind == OPENREF_BOOT_DECISION_RECOVERY);
    return 0;
}
