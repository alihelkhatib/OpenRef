#ifndef OPENREF_BOOT_CONFIRMATION_H
#define OPENREF_BOOT_CONFIRMATION_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_boot_policy.h"

typedef struct {
    bool clocks_ok;
    bool storage_ok;
    bool watchdog_ok;
    bool critical_peripherals_ok;
    bool peer_ok;
    bool running_image_authenticated;
} openref_boot_confirmation_inputs_t;

typedef bool (*openref_boot_confirmation_persist_fn)(
    void *context, const openref_boot_state_t *state);

typedef struct {
    openref_boot_confirmation_persist_fn persist;
    void *context;
} openref_boot_confirmation_backend_t;

typedef struct {
    openref_boot_state_t boot_state;
    openref_boot_slot_t slots[2];
    openref_boot_confirmation_backend_t backend;
    uint64_t soak_ms;
    uint64_t healthy_since_ms;
    uint64_t last_now_ms;
    uint32_t interrupted_soaks;
    uint32_t clock_faults;
    uint32_t persistence_failures;
    uint8_t running_slot;
    bool healthy_period_active;
    bool persistence_fault_latched;
    bool confirmed;
    bool initialized;
} openref_boot_confirmation_t;

bool openref_boot_confirmation_init(
    openref_boot_confirmation_t *confirmation,
    const openref_boot_state_t *boot_state,
    const openref_boot_slot_t slots[2],
    uint8_t running_slot,
    uint64_t soak_ms,
    openref_boot_confirmation_backend_t backend,
    uint64_t now_ms);

bool openref_boot_confirmation_tick(
    openref_boot_confirmation_t *confirmation,
    const openref_boot_confirmation_inputs_t *inputs,
    uint64_t now_ms);

#endif
