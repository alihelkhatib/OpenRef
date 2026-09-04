#ifndef OPENREF_RT595_BOOTSTRAP_H
#define OPENREF_RT595_BOOTSTRAP_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_rt595_boot_coordinator.h"
#include "openref_rt595_boot_handoff.h"

typedef bool (*openref_rt595_bootstrap_prepare_fn)(
    void *context, const openref_rt595_boot_handoff_layout_t *layout,
    openref_rt595_boot_handoff_plan_t *plan);
typedef void (*openref_rt595_bootstrap_transfer_fn)(
    void *context, const openref_rt595_boot_handoff_plan_t *plan);
typedef void (*openref_rt595_bootstrap_recovery_fn)(void *context);

typedef enum {
    OPENREF_RT595_BOOTSTRAP_RECOVERY_CONFIGURATION = 1,
    OPENREF_RT595_BOOTSTRAP_RECOVERY_DURABLE_STATE,
    OPENREF_RT595_BOOTSTRAP_RECOVERY_FLASH_READ,
    OPENREF_RT595_BOOTSTRAP_RECOVERY_NO_AUTHENTICATED_IMAGE,
    OPENREF_RT595_BOOTSTRAP_RECOVERY_POLICY,
    OPENREF_RT595_BOOTSTRAP_RECOVERY_VECTOR,
    OPENREF_RT595_BOOTSTRAP_RECOVERY_TRANSFER_RETURNED,
} openref_rt595_bootstrap_recovery_reason_t;
typedef void (*openref_rt595_bootstrap_status_fn)(void *context,
    openref_rt595_bootstrap_recovery_reason_t reason);

typedef struct {
    openref_rt595_boot_coordinator_t *coordinator;
    uint32_t image_base[2];
    uint32_t image_capacity[2];
    uint32_t authenticated_image_size[2];
    uint32_t ram_base;
    uint32_t ram_size;
    uint32_t vtor_alignment;
    openref_rt595_bootstrap_prepare_fn prepare;
    openref_rt595_bootstrap_transfer_fn transfer;
    openref_rt595_bootstrap_recovery_fn recovery;
    openref_rt595_bootstrap_status_fn status;
    openref_rt595_bootstrap_recovery_reason_t last_recovery_reason;
    void *context;
} openref_rt595_bootstrap_t;

/* Returns only if recovery returns. A production transfer must not return. */
bool openref_rt595_bootstrap_run(openref_rt595_bootstrap_t *bootstrap);

/* Separated for deterministic testing of the authenticated decision-to-jump
 * boundary. It still fails closed if transfer unexpectedly returns. */
bool openref_rt595_bootstrap_handoff(openref_rt595_bootstrap_t *bootstrap,
    const openref_boot_decision_t *decision, const openref_boot_slot_t slots[2]);

#endif
