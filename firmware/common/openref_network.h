#ifndef OPENREF_NETWORK_H
#define OPENREF_NETWORK_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_NETWORK_MAX_NODES 6u
#define OPENREF_NETWORK_BROADCAST_ID 0u
#define OPENREF_NETWORK_SUPERFRAME_US 20000u
#define OPENREF_NETWORK_SLOT_SPACING_US 2500u
#define OPENREF_NETWORK_HEARTBEAT_INTERVAL_US 100000u
#define OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US 300000u
#define OPENREF_NETWORK_ELECTION_DELAY_US 50000u

typedef enum {
    OPENREF_NETWORK_FOLLOWER = 0,
    OPENREF_NETWORK_COORDINATOR = 1,
    OPENREF_NETWORK_ELECTION = 2
} openref_network_role_t;

typedef enum {
    OPENREF_NETWORK_ACTION_NONE = 0,
    OPENREF_NETWORK_ACTION_SEND_HEARTBEAT = 1u << 0,
    OPENREF_NETWORK_ACTION_COORDINATOR_TIMEOUT = 1u << 1,
    OPENREF_NETWORK_ACTION_COORDINATOR_CHANGED = 1u << 2
} openref_network_action_t;

typedef enum {
    OPENREF_NETWORK_RX_FIRST = 0,
    OPENREF_NETWORK_RX_IN_ORDER,
    OPENREF_NETWORK_RX_GAP,
    OPENREF_NETWORK_RX_DUPLICATE,
    OPENREF_NETWORK_RX_STALE,
    OPENREF_NETWORK_RX_INVALID
} openref_network_rx_result_t;

typedef struct {
    uint8_t node_id;
    uint8_t initial_coordinator_id;
    uint8_t member_mask;
    uint32_t superframe_us;
    uint32_t slot_spacing_us;
    uint32_t heartbeat_interval_us;
    uint32_t heartbeat_timeout_us;
    uint32_t election_delay_us;
} openref_network_config_t;

typedef struct {
    bool initialized;
    uint16_t last_sequence;
    uint64_t last_tx_timestamp_us;
    uint32_t received;
    uint32_t gaps;
    uint32_t duplicates;
    uint32_t stale;
} openref_network_rx_state_t;

typedef struct {
    openref_network_config_t config;
    openref_network_role_t role;
    uint8_t coordinator_id;
    uint8_t eligible_mask;
    uint32_t coordinator_epoch;
    uint64_t schedule_origin_us;
    uint64_t last_heartbeat_us;
    uint64_t next_heartbeat_us;
    uint64_t election_deadline_us;
    uint32_t coordinator_changes;
    uint32_t heartbeat_timeouts;
    openref_network_rx_state_t rx[OPENREF_NETWORK_MAX_NODES];
} openref_network_state_t;

openref_network_config_t openref_network_default_config(uint8_t node_id);

bool openref_network_init(
    openref_network_state_t *state,
    const openref_network_config_t *config,
    uint64_t now_us);

uint32_t openref_network_tick(openref_network_state_t *state, uint64_t now_us);

bool openref_network_receive_heartbeat(
    openref_network_state_t *state,
    uint8_t coordinator_id,
    uint32_t coordinator_epoch,
    uint64_t schedule_origin_us,
    uint64_t now_us);

bool openref_network_set_member_eligible(
    openref_network_state_t *state,
    uint8_t node_id,
    bool eligible);

bool openref_network_next_slot_us(
    const openref_network_state_t *state,
    uint64_t not_before_us,
    uint64_t *slot_us);

openref_network_rx_result_t openref_network_receive_audio(
    openref_network_state_t *state,
    uint8_t source_id,
    uint16_t sequence,
    uint16_t *missing_packets);

openref_network_rx_result_t openref_network_receive_audio_timestamped(
    openref_network_state_t *state,
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    uint16_t *missing_packets);

#ifdef __cplusplus
}
#endif

#endif
