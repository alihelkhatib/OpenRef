#include "openref_boot_confirmation.h"

#include <stddef.h>
#include <string.h>

static bool all_healthy(const openref_boot_confirmation_inputs_t *inputs)
{
    return inputs->clocks_ok && inputs->storage_ok && inputs->watchdog_ok &&
        inputs->critical_peripherals_ok && inputs->peer_ok &&
        inputs->running_image_authenticated;
}

bool openref_boot_confirmation_init(
    openref_boot_confirmation_t *confirmation,
    const openref_boot_state_t *boot_state,
    const openref_boot_slot_t slots[2],
    uint8_t running_slot,
    uint64_t soak_ms,
    openref_boot_confirmation_backend_t backend,
    uint64_t now_ms)
{
    if (confirmation == NULL || boot_state == NULL || slots == NULL ||
        backend.persist == NULL || soak_ms == 0u ||
        !openref_boot_policy_state_valid(boot_state) ||
        running_slot > OPENREF_BOOT_SLOT_B ||
        boot_state->pending_slot != running_slot ||
        !slots[running_slot].present || !slots[running_slot].authenticated ||
        slots[running_slot].version < boot_state->minimum_version) {
        return false;
    }
    memset(confirmation, 0, sizeof(*confirmation));
    confirmation->boot_state = *boot_state;
    memcpy(confirmation->slots, slots, sizeof(confirmation->slots));
    confirmation->backend = backend;
    confirmation->soak_ms = soak_ms;
    confirmation->running_slot = running_slot;
    confirmation->last_now_ms = now_ms;
    confirmation->initialized = true;
    return true;
}

bool openref_boot_confirmation_tick(
    openref_boot_confirmation_t *confirmation,
    const openref_boot_confirmation_inputs_t *inputs,
    uint64_t now_ms)
{
    if (confirmation == NULL || inputs == NULL || !confirmation->initialized ||
        confirmation->confirmed || confirmation->persistence_fault_latched) {
        return false;
    }
    if (now_ms < confirmation->last_now_ms) {
        confirmation->clock_faults++;
        confirmation->healthy_period_active = false;
        confirmation->last_now_ms = now_ms;
        return false;
    }
    confirmation->last_now_ms = now_ms;
    if (!all_healthy(inputs)) {
        if (confirmation->healthy_period_active) {
            confirmation->interrupted_soaks++;
        }
        confirmation->healthy_period_active = false;
        return false;
    }
    if (!confirmation->healthy_period_active) {
        confirmation->healthy_period_active = true;
        confirmation->healthy_since_ms = now_ms;
        return false;
    }
    if (now_ms - confirmation->healthy_since_ms < confirmation->soak_ms) {
        return false;
    }
    openref_boot_state_t confirmed_state = confirmation->boot_state;
    if (!openref_boot_policy_confirm(
            &confirmed_state, confirmation->running_slot, confirmation->slots) ||
        !confirmation->backend.persist(confirmation->backend.context,
                                       &confirmed_state)) {
        confirmation->persistence_failures++;
        confirmation->persistence_fault_latched = true;
        return false;
    }
    confirmation->boot_state = confirmed_state;
    confirmation->confirmed = true;
    return true;
}
