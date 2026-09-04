#ifndef OPENREF_RT595_BOOT_STATE_H
#define OPENREF_RT595_BOOT_STATE_H
#include <stdbool.h>
#include <stdint.h>
#include "openref_boot_policy.h"
#include "openref_config_store.h"

#define OPENREF_RT595_BOOT_STATE_SCHEMA 1u
#define OPENREF_RT595_BOOT_STATE_PAYLOAD_BYTES 12u

typedef struct {
    openref_config_store_t store;
    openref_boot_state_t state;
    bool loaded;
} openref_rt595_boot_state_store_t;

bool openref_rt595_boot_state_init(openref_rt595_boot_state_store_t *, openref_config_backend_t);
bool openref_rt595_boot_state_load(openref_rt595_boot_state_store_t *);
bool openref_rt595_boot_state_initialize(openref_rt595_boot_state_store_t *, uint8_t, uint32_t);
bool openref_rt595_boot_state_stage(openref_rt595_boot_state_store_t *, uint8_t, const openref_boot_slot_t[2]);
openref_boot_decision_t openref_rt595_boot_state_select(openref_rt595_boot_state_store_t *, const openref_boot_slot_t[2], uint8_t);
bool openref_rt595_boot_state_confirm(openref_rt595_boot_state_store_t *, uint8_t, const openref_boot_slot_t[2]);
#endif
