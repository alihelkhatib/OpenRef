#ifndef OPENREF_PEER_SUPERVISOR_H
#define OPENREF_PEER_SUPERVISOR_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_PEER_HEALTHY = 0,
    OPENREF_PEER_RESET_ASSERTED = 1,
    OPENREF_PEER_BOOT_WAIT = 2,
    OPENREF_PEER_POWER_CYCLE_WAIT = 3,
    OPENREF_PEER_FAILED = 4
} openref_peer_state_t;

#define OPENREF_PEER_ACTION_MUTE_AUDIO (1u << 0)
#define OPENREF_PEER_ACTION_ASSERT_RESET (1u << 1)
#define OPENREF_PEER_ACTION_RELEASE_RESET (1u << 2)
#define OPENREF_PEER_ACTION_POWER_CYCLE (1u << 3)
#define OPENREF_PEER_ACTION_REPORT_FAULT (1u << 4)

typedef struct {
    uint32_t heartbeat_timeout_ms;
    uint32_t reset_hold_ms;
    uint32_t boot_wait_ms;
    uint32_t power_cycle_wait_ms;
    uint8_t maximum_reset_attempts;
} openref_peer_config_t;

typedef struct {
    openref_peer_config_t config;
    openref_peer_state_t state;
    uint64_t last_heartbeat_ms;
    uint64_t state_since_ms;
    uint8_t reset_attempts;
    uint32_t heartbeat_count;
    uint32_t timeout_count;
    uint32_t recovery_count;
    uint32_t power_cycle_count;
} openref_peer_supervisor_t;

bool openref_peer_supervisor_init(
    openref_peer_supervisor_t *supervisor,
    const openref_peer_config_t *config,
    uint64_t now_ms);

void openref_peer_supervisor_heartbeat(
    openref_peer_supervisor_t *supervisor,
    uint64_t now_ms);

uint32_t openref_peer_supervisor_tick(
    openref_peer_supervisor_t *supervisor,
    uint64_t now_ms);

#endif
