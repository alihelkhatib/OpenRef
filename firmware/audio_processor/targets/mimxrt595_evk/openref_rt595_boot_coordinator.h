#ifndef OPENREF_RT595_BOOT_COORDINATOR_H
#define OPENREF_RT595_BOOT_COORDINATOR_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_rt595_boot_state.h"
#include "openref_rt595_slot_authenticator.h"

typedef struct {
    openref_rt595_slot_authenticator_t *authenticator;
    openref_rt595_boot_state_store_t *state_store;
    uint8_t maximum_trial_attempts;
} openref_rt595_boot_coordinator_t;

bool openref_rt595_boot_coordinator_init(
    openref_rt595_boot_coordinator_t *coordinator,
    openref_rt595_slot_authenticator_t *authenticator,
    openref_rt595_boot_state_store_t *state_store,
    uint8_t maximum_trial_attempts);

openref_boot_decision_t openref_rt595_boot_coordinator_select(
    openref_rt595_boot_coordinator_t *coordinator,
    openref_boot_slot_t authenticated_slots[2]);

#endif
