#include "openref_network_fg23.h"

#ifdef OPENREF_APP_NETWORK

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "app_common.h"
#include "openref_network.h"
#include "openref_network_packet.h"

#ifndef OPENREF_APP_NETWORK_NODE_ID
#define OPENREF_APP_NETWORK_NODE_ID 1u
#endif

#define OPENREF_NETWORK_MEMBER_MASK 0x0fu
#define OPENREF_NETWORK_SCHEDULE_LEAD_US 3000u
#define OPENREF_NETWORK_CONTROL_SLOT_US 15000u
#define OPENREF_NETWORK_REPORT_EVERY 250u

static openref_network_state_t network_state;
static bool network_configured;
static bool tx_pending;
static bool heartbeat_pending;
static bool schedule_synchronized;
static uint16_t audio_sequence;
static uint16_t heartbeat_sequence;
static uint32_t tx_completion_snapshot;
static uint32_t tx_success_snapshot;
static uint64_t next_audio_slot_us;
static uint64_t next_control_slot_us;
static uint32_t rx_packets;
static uint32_t parse_failures;
static uint32_t schedule_failures;

static uint32_t tx_completion_count(void)
{
    return counters.userTx + counters.userTxAborted + counters.userTxBlocked +
        counters.userTxUnderflow;
}

static uint64_t next_periodic_slot(
    uint64_t origin_us,
    uint32_t offset_us,
    uint32_t period_us,
    uint64_t not_before_us)
{
    uint64_t candidate = origin_us + offset_us;
    if (candidate < not_before_us) {
        uint64_t elapsed = not_before_us - candidate;
        candidate += ((elapsed + period_us - 1u) / period_us) * period_us;
    }
    return candidate;
}

static void start_rx(void)
{
    rxHeld = true;
    (void)RAIL_StartRx(railHandle, channel, NULL);
}

static void process_rx(void)
{
    while (packetsHeld > 0u) {
        RAIL_RxPacketInfo_t info;
        RAIL_RxPacketHandle_t handle = RAIL_GetRxPacketInfo(
            railHandle, RAIL_RX_PACKET_HANDLE_OLDEST_COMPLETE, &info);
        if (handle == RAIL_RX_PACKET_HANDLE_INVALID) {
            return;
        }

        uint8_t packet[OPENREF_NETWORK_PACKET_BYTES];
        bool copied = info.packetStatus == RAIL_RX_PACKET_READY_SUCCESS &&
            info.packetBytes == sizeof(packet);
        if (copied) {
            RAIL_CopyRxPacket(packet, &info);
        }
        (void)RAIL_ReleaseRxPacket(railHandle, handle);
        if (packetsHeld > 0u) {
            packetsHeld--;
        }

        openref_proto0_packet_header_t header;
        if (!copied || !openref_network_parse_packet(packet, sizeof(packet), &header)) {
            parse_failures++;
            continue;
        }
        if (header.source_id == network_state.config.node_id) {
            continue;
        }

        rx_packets++;
        if (header.kind == OPENREF_PROTO0_PACKET_HEARTBEAT) {
            openref_network_heartbeat_t heartbeat;
            if (!openref_network_parse_heartbeat(packet, sizeof(packet), &heartbeat) ||
                !openref_network_receive_heartbeat(
                    &network_state,
                    header.source_id,
                    heartbeat.coordinator_epoch,
                    heartbeat.schedule_origin_us,
                    RAIL_GetTime())) {
                parse_failures++;
            } else {
                schedule_synchronized = true;
                next_audio_slot_us = next_periodic_slot(
                    network_state.schedule_origin_us,
                    (network_state.config.node_id - 1u) * network_state.config.slot_spacing_us,
                    network_state.config.superframe_us,
                    (uint64_t)RAIL_GetTime() + OPENREF_NETWORK_SCHEDULE_LEAD_US);
            }
        } else if (header.kind == OPENREF_PROTO0_PACKET_AUDIO_FRAME) {
            uint16_t missing = 0u;
            openref_network_rx_result_t result = openref_network_receive_audio_timestamped(
                &network_state,
                header.source_id,
                header.sequence,
                header.tx_timestamp_us,
                &missing);
            if (result == OPENREF_NETWORK_RX_GAP ||
                result == OPENREF_NETWORK_RX_DUPLICATE ||
                result == OPENREF_NETWORK_RX_STALE) {
                printf("\r\n{{(openrefNetRx)}{Node:%u}{Source:%u}{Sequence:%u}{Result:%u}{Missing:%u}}}\r\n",
                       (unsigned int)network_state.config.node_id,
                       (unsigned int)header.source_id,
                       (unsigned int)header.sequence,
                       (unsigned int)result,
                       (unsigned int)missing);
            }
        }

        if ((rx_packets % OPENREF_NETWORK_REPORT_EVERY) == 0u) {
            printf("\r\n{{(openrefNetRx)}{Node:%u}{Packets:%lu}{ParseFail:%lu}{ScheduleFail:%lu}{Coordinator:%u}{Epoch:%lu}}}\r\n",
                   (unsigned int)network_state.config.node_id,
                   (unsigned long)rx_packets,
                   (unsigned long)parse_failures,
                   (unsigned long)schedule_failures,
                   (unsigned int)network_state.coordinator_id,
                   (unsigned long)network_state.coordinator_epoch);
        }
    }
}

static bool schedule_packet(bool heartbeat, uint64_t scheduled_us)
{
    uint8_t packet[OPENREF_NETWORK_PACKET_BYTES];
    uint16_t length;
    if (heartbeat) {
        openref_network_heartbeat_t body = {
            .coordinator_epoch = network_state.coordinator_epoch,
            .schedule_origin_us = network_state.schedule_origin_us,
        };
        length = openref_network_build_heartbeat_packet(
            network_state.config.node_id,
            ++heartbeat_sequence,
            scheduled_us,
            &body,
            packet,
            sizeof(packet));
    } else {
        length = openref_network_build_audio_packet(
            network_state.config.node_id,
            ++audio_sequence,
            scheduled_us,
            packet,
            sizeof(packet));
    }
    if (length != sizeof(packet) ||
        RAIL_WriteTxFifo(railHandle, packet, length, true) != length) {
        schedule_failures++;
        return false;
    }

    RAIL_ScheduleTxConfig_t config = {
        .when = (RAIL_Time_t)scheduled_us,
        .mode = RAIL_TIME_ABSOLUTE,
        .txDuringRx = RAIL_SCHEDULED_TX_DURING_RX_POSTPONE_TX,
    };
    tx_completion_snapshot = tx_completion_count();
    tx_success_snapshot = counters.userTx;
    RAIL_Status_t status = RAIL_StartScheduledTx(
        railHandle, channel, RAIL_TX_OPTIONS_DEFAULT, &config, NULL);
    if (status != RAIL_STATUS_NO_ERROR) {
        schedule_failures++;
        start_rx();
        return false;
    }
    tx_pending = true;
    return true;
}

void openref_network_fg23_init(void)
{
    network_configured = false;
}

void openref_network_fg23_process(void)
{
    if (railHandle == NULL) {
        return;
    }
    if (!network_configured) {
        openref_network_config_t config =
            openref_network_default_config((uint8_t)OPENREF_APP_NETWORK_NODE_ID);
        config.member_mask = OPENREF_NETWORK_MEMBER_MASK;
        uint64_t now_us = RAIL_GetTime();
        if (!openref_network_init(&network_state, &config, now_us)) {
            printf("\r\n{{(openrefNetwork)}{Status:SelfTestFail}{Node:%u}}}\r\n",
                   (unsigned int)config.node_id);
            return;
        }
        uint16_t fixed_length = RAIL_SetFixedLength(railHandle, OPENREF_NETWORK_PACKET_BYTES);
        RAIL_ConfigEvents(
            railHandle,
            RAIL_EVENT_TX_STARTED | RAIL_EVENTS_TX_COMPLETION,
            RAIL_EVENT_TX_STARTED | RAIL_EVENTS_TX_COMPLETION);
        logLevel &= (uint8_t)~ASYNC_RESPONSE;
        next_audio_slot_us = next_periodic_slot(
            network_state.schedule_origin_us,
            (config.node_id - 1u) * config.slot_spacing_us,
            config.superframe_us,
            now_us + OPENREF_NETWORK_SCHEDULE_LEAD_US);
        next_control_slot_us = next_periodic_slot(
            network_state.schedule_origin_us,
            OPENREF_NETWORK_CONTROL_SLOT_US,
            config.superframe_us,
            now_us + OPENREF_NETWORK_SCHEDULE_LEAD_US);
        start_rx();
        schedule_synchronized = network_state.role == OPENREF_NETWORK_COORDINATOR;
        network_configured = true;
        printf("\r\n{{(openrefNetwork)}{Status:Ready}{Node:%u}{Coordinator:%u}{Role:%u}{FixedLength:%u}{NextSlotUs:%lu}}}\r\n",
               (unsigned int)config.node_id,
               (unsigned int)network_state.coordinator_id,
               (unsigned int)network_state.role,
               (unsigned int)fixed_length,
               (unsigned long)next_audio_slot_us);
        return;
    }

    process_rx();
    uint64_t now_us = RAIL_GetTime();
    uint32_t actions = openref_network_tick(&network_state, now_us);
    if ((actions & OPENREF_NETWORK_ACTION_SEND_HEARTBEAT) != 0u) {
        heartbeat_pending = true;
    }
    if ((actions & OPENREF_NETWORK_ACTION_COORDINATOR_TIMEOUT) != 0u) {
        schedule_synchronized = false;
    }
    if ((actions & OPENREF_NETWORK_ACTION_COORDINATOR_CHANGED) != 0u) {
        schedule_synchronized = network_state.role == OPENREF_NETWORK_COORDINATOR;
    }
    if ((actions & (OPENREF_NETWORK_ACTION_COORDINATOR_TIMEOUT |
                    OPENREF_NETWORK_ACTION_COORDINATOR_CHANGED)) != 0u) {
        printf("\r\n{{(openrefElection)}{Node:%u}{Actions:%lu}{Coordinator:%u}{Epoch:%lu}{Role:%u}}}\r\n",
               (unsigned int)network_state.config.node_id,
               (unsigned long)actions,
               (unsigned int)network_state.coordinator_id,
               (unsigned long)network_state.coordinator_epoch,
               (unsigned int)network_state.role);
    }

    if (tx_pending) {
        if (tx_completion_count() > tx_completion_snapshot) {
            tx_pending = false;
            if (counters.userTx == tx_success_snapshot) {
                schedule_failures++;
            }
            start_rx();
        } else {
            return;
        }
    }

    if (!schedule_synchronized) {
        return;
    }

    if (next_audio_slot_us <= now_us + OPENREF_NETWORK_SCHEDULE_LEAD_US) {
        next_audio_slot_us = next_periodic_slot(
            network_state.schedule_origin_us,
            (network_state.config.node_id - 1u) * network_state.config.slot_spacing_us,
            network_state.config.superframe_us,
            now_us + OPENREF_NETWORK_SCHEDULE_LEAD_US);
    }
    if (next_control_slot_us <= now_us + OPENREF_NETWORK_SCHEDULE_LEAD_US) {
        next_control_slot_us = next_periodic_slot(
            network_state.schedule_origin_us,
            OPENREF_NETWORK_CONTROL_SLOT_US,
            network_state.config.superframe_us,
            now_us + OPENREF_NETWORK_SCHEDULE_LEAD_US);
    }

    if (heartbeat_pending && next_control_slot_us < next_audio_slot_us) {
        if (schedule_packet(true, next_control_slot_us)) {
            heartbeat_pending = false;
            next_control_slot_us += network_state.config.superframe_us;
        }
    } else if (schedule_packet(false, next_audio_slot_us)) {
        next_audio_slot_us += network_state.config.superframe_us;
    }
}

#else

void openref_network_fg23_init(void) {}
void openref_network_fg23_process(void) {}

#endif
