#ifndef OPENREF_BOOT_POLICY_H
#define OPENREF_BOOT_POLICY_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_BOOT_SLOT_A 0u
#define OPENREF_BOOT_SLOT_B 1u
#define OPENREF_BOOT_NO_SLOT 0xffu

typedef enum {
    OPENREF_BOOT_DECISION_NONE = 0,
    OPENREF_BOOT_DECISION_CONFIRMED = 1,
    OPENREF_BOOT_DECISION_TRIAL = 2,
    OPENREF_BOOT_DECISION_FALLBACK = 3,
    OPENREF_BOOT_DECISION_RECOVERY = 4
} openref_boot_decision_kind_t;

typedef struct {
    bool present;
    bool authenticated;
    uint32_t version;
} openref_boot_slot_t;

typedef struct {
    uint32_t record_version;
    uint32_t minimum_version;
    uint8_t confirmed_slot;
    uint8_t pending_slot;
    uint8_t pending_attempts;
} openref_boot_state_t;

typedef struct {
    uint8_t slot;
    openref_boot_decision_kind_t kind;
    bool state_changed;
} openref_boot_decision_t;

bool openref_boot_policy_state_valid(const openref_boot_state_t *state);

bool openref_boot_policy_stage(
    openref_boot_state_t *state,
    uint8_t candidate_slot,
    const openref_boot_slot_t slots[2]);

openref_boot_decision_t openref_boot_policy_select(
    openref_boot_state_t *state,
    const openref_boot_slot_t slots[2],
    uint8_t maximum_trial_attempts);

bool openref_boot_policy_confirm(
    openref_boot_state_t *state,
    uint8_t running_slot,
    const openref_boot_slot_t slots[2]);

#endif
