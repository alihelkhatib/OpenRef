#include "openref_network.h"

#include <stddef.h>
#include <string.h>

static bool valid_node_id(uint8_t node_id)
{
    return node_id >= 1u && node_id <= OPENREF_NETWORK_MAX_NODES;
}

static bool member_present(uint8_t mask, uint8_t node_id)
{
    return valid_node_id(node_id) && (mask & (uint8_t)(1u << (node_id - 1u))) != 0u;
}

static uint8_t elect_lowest_member(uint8_t mask)
{
    for (uint8_t node_id = 1u; node_id <= OPENREF_NETWORK_MAX_NODES; node_id++) {
        if (member_present(mask, node_id)) {
            return node_id;
        }
    }
    return OPENREF_NETWORK_BROADCAST_ID;
}

static uint64_t advance_periodic(uint64_t deadline, uint32_t period, uint64_t now_us)
{
    if (deadline > now_us) {
        return deadline;
    }
    uint64_t elapsed = now_us - deadline;
    return deadline + ((elapsed / period) + 1u) * period;
}

openref_network_config_t openref_network_default_config(uint8_t node_id)
{
    openref_network_config_t config = {
        .node_id = node_id,
        .initial_coordinator_id = 1u,
        .member_mask = 0x3fu,
        .superframe_us = OPENREF_NETWORK_SUPERFRAME_US,
        .slot_spacing_us = OPENREF_NETWORK_SLOT_SPACING_US,
        .heartbeat_interval_us = OPENREF_NETWORK_HEARTBEAT_INTERVAL_US,
        .heartbeat_timeout_us = OPENREF_NETWORK_HEARTBEAT_TIMEOUT_US,
        .election_delay_us = OPENREF_NETWORK_ELECTION_DELAY_US,
        .initial_coordinator_epoch = 0u,
    };
    return config;
}

bool openref_network_init(
    openref_network_state_t *state,
    const openref_network_config_t *config,
    uint64_t now_us)
{
    if (state == NULL || config == NULL ||
        !valid_node_id(config->node_id) ||
        !member_present(config->member_mask, config->node_id) ||
        !member_present(config->member_mask, config->initial_coordinator_id) ||
        config->superframe_us == 0u || config->slot_spacing_us == 0u ||
        config->heartbeat_interval_us == 0u || config->heartbeat_timeout_us == 0u ||
        config->election_delay_us == 0u ||
        (config->require_persisted_epoch && config->advance_epoch == NULL) ||
        (uint64_t)OPENREF_NETWORK_MAX_NODES * config->slot_spacing_us > config->superframe_us) {
        return false;
    }

    memset(state, 0, sizeof(*state));
    state->config = *config;
    state->eligible_mask = config->member_mask;
    state->coordinator_id = config->initial_coordinator_id;
    state->coordinator_epoch = config->initial_coordinator_epoch;
    state->role = config->node_id == config->initial_coordinator_id
        ? OPENREF_NETWORK_COORDINATOR
        : OPENREF_NETWORK_FOLLOWER;
    state->schedule_origin_us = now_us;
    state->last_heartbeat_us = now_us;
    state->next_heartbeat_us = now_us + config->heartbeat_interval_us;
    return true;
}

uint32_t openref_network_tick(openref_network_state_t *state, uint64_t now_us)
{
    if (state == NULL) {
        return OPENREF_NETWORK_ACTION_NONE;
    }

    uint32_t actions = OPENREF_NETWORK_ACTION_NONE;
    if (state->role == OPENREF_NETWORK_COORDINATOR) {
        if (now_us >= state->next_heartbeat_us) {
            actions |= OPENREF_NETWORK_ACTION_SEND_HEARTBEAT;
            state->next_heartbeat_us = advance_periodic(
                state->next_heartbeat_us,
                state->config.heartbeat_interval_us,
                now_us);
        }
        return actions;
    }

    if (state->role == OPENREF_NETWORK_FOLLOWER &&
        now_us - state->last_heartbeat_us > state->config.heartbeat_timeout_us) {
        state->eligible_mask &= (uint8_t)~(1u << (state->coordinator_id - 1u));
        state->role = OPENREF_NETWORK_ELECTION;
        state->election_deadline_us = now_us + state->config.election_delay_us;
        state->heartbeat_timeouts++;
        actions |= OPENREF_NETWORK_ACTION_COORDINATOR_TIMEOUT;
    }

    if (state->role == OPENREF_NETWORK_ELECTION && now_us >= state->election_deadline_us) {
        uint8_t elected = elect_lowest_member(state->eligible_mask);
        if (elected != OPENREF_NETWORK_BROADCAST_ID) {
            uint32_t next_epoch = 0u;
            bool epoch_advanced = false;
            if (state->config.advance_epoch != NULL) {
                epoch_advanced = state->config.advance_epoch(
                    state->config.epoch_context, state->coordinator_epoch,
                    &next_epoch) && next_epoch > state->coordinator_epoch;
            } else if (!state->config.require_persisted_epoch &&
                       state->coordinator_epoch != UINT32_MAX) {
                next_epoch = state->coordinator_epoch + 1u;
                epoch_advanced = true;
            }
            if (!epoch_advanced) {
                state->epoch_failures++;
                state->election_deadline_us = now_us +
                    state->config.election_delay_us;
                return actions | OPENREF_NETWORK_ACTION_EPOCH_FAILURE;
            }
            state->coordinator_id = elected;
            state->coordinator_epoch = next_epoch;
            state->role = elected == state->config.node_id
                ? OPENREF_NETWORK_COORDINATOR
                : OPENREF_NETWORK_FOLLOWER;
            state->last_heartbeat_us = now_us;
            state->schedule_origin_us = now_us;
            state->next_heartbeat_us = now_us;
            state->coordinator_changes++;
            actions |= OPENREF_NETWORK_ACTION_COORDINATOR_CHANGED;
            if (state->role == OPENREF_NETWORK_COORDINATOR) {
                actions |= OPENREF_NETWORK_ACTION_SEND_HEARTBEAT;
                state->next_heartbeat_us = now_us + state->config.heartbeat_interval_us;
            }
        }
    }
    return actions;
}

bool openref_network_receive_heartbeat(
    openref_network_state_t *state,
    uint8_t coordinator_id,
    uint32_t coordinator_epoch,
    uint64_t schedule_origin_us,
    uint64_t now_us)
{
    if (state == NULL || !member_present(state->config.member_mask, coordinator_id)) {
        return false;
    }
    if (coordinator_epoch < state->coordinator_epoch ||
        (coordinator_epoch == state->coordinator_epoch &&
         coordinator_id > state->coordinator_id)) {
        return false;
    }

    if (coordinator_id != state->coordinator_id) {
        state->coordinator_changes++;
    }
    state->eligible_mask |= (uint8_t)(1u << (coordinator_id - 1u));
    state->coordinator_id = coordinator_id;
    state->coordinator_epoch = coordinator_epoch;
    state->schedule_origin_us = schedule_origin_us;
    state->last_heartbeat_us = now_us;
    state->role = coordinator_id == state->config.node_id
        ? OPENREF_NETWORK_COORDINATOR
        : OPENREF_NETWORK_FOLLOWER;
    if (state->role == OPENREF_NETWORK_COORDINATOR) {
        state->next_heartbeat_us = now_us + state->config.heartbeat_interval_us;
    }
    return true;
}

bool openref_network_set_member_eligible(
    openref_network_state_t *state,
    uint8_t node_id,
    bool eligible)
{
    if (state == NULL || !member_present(state->config.member_mask, node_id)) {
        return false;
    }
    uint8_t bit = (uint8_t)(1u << (node_id - 1u));
    if (eligible) {
        state->eligible_mask |= bit;
    } else {
        state->eligible_mask &= (uint8_t)~bit;
    }
    return true;
}

bool openref_network_next_slot_us(
    const openref_network_state_t *state,
    uint64_t not_before_us,
    uint64_t *slot_us)
{
    if (state == NULL || slot_us == NULL || !valid_node_id(state->config.node_id)) {
        return false;
    }
    uint64_t offset = (uint64_t)(state->config.node_id - 1u) * state->config.slot_spacing_us;
    uint64_t candidate = state->schedule_origin_us + offset;
    if (candidate < not_before_us) {
        uint64_t elapsed = not_before_us - candidate;
        candidate += ((elapsed + state->config.superframe_us - 1u) /
                      state->config.superframe_us) * state->config.superframe_us;
    }
    *slot_us = candidate;
    return true;
}

openref_network_rx_result_t openref_network_receive_audio(
    openref_network_state_t *state,
    uint8_t source_id,
    uint16_t sequence,
    uint16_t *missing_packets)
{
    return openref_network_receive_audio_timestamped(
        state, source_id, sequence, 0u, missing_packets);
}

openref_network_rx_result_t openref_network_receive_audio_timestamped(
    openref_network_state_t *state,
    uint8_t source_id,
    uint16_t sequence,
    uint64_t tx_timestamp_us,
    uint16_t *missing_packets)
{
    if (missing_packets != NULL) {
        *missing_packets = 0u;
    }
    if (state == NULL || !valid_node_id(source_id) || source_id == state->config.node_id) {
        return OPENREF_NETWORK_RX_INVALID;
    }

    openref_network_rx_state_t *rx = &state->rx[source_id - 1u];
    if (!rx->initialized) {
        rx->initialized = true;
        rx->last_sequence = sequence;
        rx->last_tx_timestamp_us = tx_timestamp_us;
        rx->received++;
        return OPENREF_NETWORK_RX_FIRST;
    }

    if (tx_timestamp_us != 0u &&
        tx_timestamp_us < rx->last_tx_timestamp_us && sequence <= 16u) {
        rx->last_sequence = sequence;
        rx->last_tx_timestamp_us = tx_timestamp_us;
        rx->received++;
        return OPENREF_NETWORK_RX_FIRST;
    }

    uint16_t delta = (uint16_t)(sequence - rx->last_sequence);
    if (delta == 0u) {
        rx->duplicates++;
        return OPENREF_NETWORK_RX_DUPLICATE;
    }
    if (delta >= 0x8000u) {
        rx->stale++;
        return OPENREF_NETWORK_RX_STALE;
    }

    rx->last_sequence = sequence;
    if (tx_timestamp_us != 0u) {
        rx->last_tx_timestamp_us = tx_timestamp_us;
    }
    rx->received++;
    if (delta == 1u) {
        return OPENREF_NETWORK_RX_IN_ORDER;
    }

    uint16_t missing = (uint16_t)(delta - 1u);
    rx->gaps += missing;
    if (missing_packets != NULL) {
        *missing_packets = missing;
    }
    return OPENREF_NETWORK_RX_GAP;
}
