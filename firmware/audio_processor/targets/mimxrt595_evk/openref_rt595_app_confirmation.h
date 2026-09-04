#ifndef OPENREF_RT595_APP_CONFIRMATION_H
#define OPENREF_RT595_APP_CONFIRMATION_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_rt595_boot_state.h"

/* The application calls observe once per completed 10 ms audio block. */
#define OPENREF_RT595_CONFIRMATION_SAMPLE_MS 10u
#define OPENREF_RT595_CONFIRMATION_SOAK_MS 30000u
#define OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES \
    (OPENREF_RT595_CONFIRMATION_SOAK_MS / OPENREF_RT595_CONFIRMATION_SAMPLE_MS)
#define OPENREF_RT595_CONFIRMATION_MAX_SAMPLE_GAP_MS 20u

typedef struct {
    bool clocks_ok;
    bool storage_ok;
    bool watchdog_ok;
    bool audio_ok;
    bool peer_ok;
    bool fault_free;
} openref_rt595_app_health_t;

typedef enum {
    OPENREF_RT595_CONFIRMATION_INACTIVE = 0,
    OPENREF_RT595_CONFIRMATION_SOAKING = 1,
    OPENREF_RT595_CONFIRMATION_CONFIRMED = 2,
    OPENREF_RT595_CONFIRMATION_PERSIST_FAILED = 3
} openref_rt595_confirmation_status_t;

typedef struct {
    openref_rt595_boot_state_store_t *boot_state;
    openref_boot_slot_t slots[2];
    uint32_t healthy_samples;
    uint32_t first_sample_ms;
    uint32_t last_sample_ms;
    uint32_t persistence_failures;
    uint8_t running_slot;
    bool sample_time_valid;
    openref_rt595_confirmation_status_t status;
} openref_rt595_app_confirmation_t;

bool openref_rt595_app_confirmation_init(
    openref_rt595_app_confirmation_t *supervisor,
    openref_rt595_boot_state_store_t *boot_state,
    uint8_t running_slot,
    const openref_boot_slot_t slots[2]);

/* Returns true only after confirmation is durably committed. */
bool openref_rt595_app_confirmation_observe(
    openref_rt595_app_confirmation_t *supervisor,
    openref_rt595_app_health_t health,
    uint32_t monotonic_ms);

/* Call from every application fault path before reset/shutdown. */
void openref_rt595_app_confirmation_fault(
    openref_rt595_app_confirmation_t *supervisor);

#endif
