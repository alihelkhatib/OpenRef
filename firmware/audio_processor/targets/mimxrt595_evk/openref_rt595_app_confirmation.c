#include "openref_rt595_app_confirmation.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static bool all_healthy(openref_rt595_app_health_t h)
{
    return h.clocks_ok && h.storage_ok && h.watchdog_ok && h.audio_ok &&
           h.peer_ok && h.fault_free;
}

static bool trial_still_matches(const openref_rt595_app_confirmation_t *s)
{
    const openref_boot_state_t *state;
    if (!s || !s->boot_state || !s->boot_state->loaded) return false;
    state = &s->boot_state->state;
    return state->pending_slot == s->running_slot &&
           state->pending_attempts > 0u &&
           state->confirmed_slot != s->running_slot;
}

bool openref_rt595_app_confirmation_init(
    openref_rt595_app_confirmation_t *s,
    openref_rt595_boot_state_store_t *boot_state,
    uint8_t running_slot,
    const openref_boot_slot_t slots[2])
{
    if (!s) return false;
    memset(s, 0, sizeof(*s));
    s->status = OPENREF_RT595_CONFIRMATION_INACTIVE;
    if (!boot_state || !slots ||
        (running_slot != OPENREF_BOOT_SLOT_A &&
         running_slot != OPENREF_BOOT_SLOT_B)) return false;
    s->boot_state = boot_state;
    s->running_slot = running_slot;
    memcpy(s->slots, slots, sizeof(s->slots));
    if (!s->slots[running_slot].present ||
        !s->slots[running_slot].authenticated ||
        !trial_still_matches(s)) return false;
    s->status = OPENREF_RT595_CONFIRMATION_SOAKING;
    return true;
}

void openref_rt595_app_confirmation_fault(openref_rt595_app_confirmation_t *s)
{
    if (!s || s->status == OPENREF_RT595_CONFIRMATION_CONFIRMED) return;
    s->healthy_samples = 0u;
    s->sample_time_valid = false;
    if (s->status != OPENREF_RT595_CONFIRMATION_INACTIVE)
        s->status = OPENREF_RT595_CONFIRMATION_SOAKING;
}

bool openref_rt595_app_confirmation_observe(
    openref_rt595_app_confirmation_t *s,
    openref_rt595_app_health_t health,
    uint32_t monotonic_ms)
{
    if (!s || s->status == OPENREF_RT595_CONFIRMATION_INACTIVE) return false;
    if (s->status == OPENREF_RT595_CONFIRMATION_CONFIRMED) return true;
    if (!trial_still_matches(s)) {
        s->healthy_samples = 0u;
        s->status = OPENREF_RT595_CONFIRMATION_INACTIVE;
        return false;
    }
    if (!all_healthy(health)) {
        openref_rt595_app_confirmation_fault(s);
        return false;
    }
    if (s->sample_time_valid) {
        uint32_t gap_ms = monotonic_ms - s->last_sample_ms;
        if (gap_ms == 0u || gap_ms > OPENREF_RT595_CONFIRMATION_MAX_SAMPLE_GAP_MS) {
            openref_rt595_app_confirmation_fault(s);
            return false;
        }
    } else {
        s->first_sample_ms = monotonic_ms;
        s->sample_time_valid = true;
    }
    s->last_sample_ms = monotonic_ms;
    s->status = OPENREF_RT595_CONFIRMATION_SOAKING;
    if (s->healthy_samples < OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES)
        ++s->healthy_samples;
    if (s->healthy_samples < OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES)
        return false;
    if ((monotonic_ms - s->first_sample_ms) <
        (OPENREF_RT595_CONFIRMATION_SOAK_MS -
         OPENREF_RT595_CONFIRMATION_SAMPLE_MS)) {
        openref_rt595_app_confirmation_fault(s);
        return false;
    }
    if (!openref_rt595_boot_state_confirm(
            s->boot_state, s->running_slot, s->slots)) {
        s->healthy_samples = 0u;
        if (s->persistence_failures != UINT32_MAX) ++s->persistence_failures;
        s->status = OPENREF_RT595_CONFIRMATION_PERSIST_FAILED;
        return false;
    }
    s->status = OPENREF_RT595_CONFIRMATION_CONFIRMED;
    return true;
}
