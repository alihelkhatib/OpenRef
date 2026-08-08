#include "openref_app.h"

#include <stdio.h>

#include "openref_packet_pair.h"

#if defined(OPENREF_APP_AUTOTX) || defined(OPENREF_APP_AUTORX) || defined(OPENREF_APP_AUTOROLE)
#include "app_common.h"
#endif

#define OPENREF_APP_AUTOTX_INTERVAL_US 350000u
#define OPENREF_APP_AUTORX_REPORT_EVERY 25u
#define OPENREF_APP_ROLE_IDLE 0u
#define OPENREF_APP_ROLE_TX 1u
#define OPENREF_APP_ROLE_RX 2u
#define OPENREF_APP_ROLE_SCHEDULED_TX 3u
#define OPENREF_APP_ROLE_MEM_REPORT 4u
#define OPENREF_APP_SCHEDTX_INTERVAL_US 20000u
#define OPENREF_APP_SCHEDTX_LEAD_US 5000u
#define OPENREF_APP_SCHEDTX_DEFAULT_ATTEMPTS 100u

static openref_packet_pair_state_t app_state;

#if defined(OPENREF_APP_AUTOTX) || defined(OPENREF_APP_AUTOROLE)
static bool autotx_configured;
static uint32_t next_autotx_us;
#endif

#if defined(OPENREF_APP_AUTORX) || defined(OPENREF_APP_AUTOROLE)
static bool autorx_configured;
#endif

#ifdef OPENREF_APP_AUTOROLE
volatile uint32_t openref_app_role;
volatile uint32_t openref_app_payload_bytes = OPENREF_PACKET_PAIR_PAYLOAD_BYTES;
volatile uint32_t openref_app_schedtx_attempts = OPENREF_APP_SCHEDTX_DEFAULT_ATTEMPTS;
static uint32_t active_role;
static bool schedtx_configured;
static bool schedtx_pending;
static bool schedtx_started_reported;
static uint32_t schedtx_next_queue_us;
static uint32_t schedtx_requested_tx_us;
static uint32_t schedtx_started_counter;
static uint32_t schedtx_done_counter;
static uint32_t schedtx_attempt_count;
static uint32_t schedtx_accept_count;
static uint32_t schedtx_reject_count;
static bool schedtx_summary_reported;
static uint16_t schedtx_sequence;
#endif

#if defined(OPENREF_APP_AUTOROLE) && defined(OPENREF_APP_GPIO_MARKERS)
#include "em_gpio.h"
#endif

#if defined(OPENREF_APP_AUTOTX) || defined(OPENREF_APP_AUTORX) || defined(OPENREF_APP_AUTOROLE)
static uint16_t openref_app_current_payload_bytes(void)
{
    uint16_t payload_bytes = OPENREF_PACKET_PAIR_PAYLOAD_BYTES;
#ifdef OPENREF_APP_AUTOROLE
    if (openref_app_payload_bytes <= OPENREF_PROTO0_MAX_PAYLOAD_BYTES) {
        payload_bytes = (uint16_t)openref_app_payload_bytes;
    }
#endif
    return payload_bytes;
}
#endif

#if defined(OPENREF_APP_AUTOROLE) && defined(OPENREF_APP_GPIO_MARKERS)
static void openref_gpio_mark_build(void)
{
#ifdef OPENREF_GPIO_BUILD_PORT
    GPIO_PinOutSet(OPENREF_GPIO_BUILD_PORT, OPENREF_GPIO_BUILD_PIN);
    GPIO_PinOutClear(OPENREF_GPIO_BUILD_PORT, OPENREF_GPIO_BUILD_PIN);
#endif
}

static void openref_gpio_mark_queue(void)
{
#ifdef OPENREF_GPIO_QUEUE_PORT
    GPIO_PinOutSet(OPENREF_GPIO_QUEUE_PORT, OPENREF_GPIO_QUEUE_PIN);
    GPIO_PinOutClear(OPENREF_GPIO_QUEUE_PORT, OPENREF_GPIO_QUEUE_PIN);
#endif
}

static void openref_gpio_mark_start(void)
{
#ifdef OPENREF_GPIO_START_PORT
    GPIO_PinOutSet(OPENREF_GPIO_START_PORT, OPENREF_GPIO_START_PIN);
    GPIO_PinOutClear(OPENREF_GPIO_START_PORT, OPENREF_GPIO_START_PIN);
#endif
}

static void openref_gpio_mark_done(void)
{
#ifdef OPENREF_GPIO_DONE_PORT
    GPIO_PinOutSet(OPENREF_GPIO_DONE_PORT, OPENREF_GPIO_DONE_PIN);
    GPIO_PinOutClear(OPENREF_GPIO_DONE_PORT, OPENREF_GPIO_DONE_PIN);
#endif
}

static void openref_gpio_init_markers(void)
{
#ifdef OPENREF_GPIO_BUILD_PORT
    GPIO_PinModeSet(OPENREF_GPIO_BUILD_PORT, OPENREF_GPIO_BUILD_PIN, gpioModePushPull, 0);
#endif
#ifdef OPENREF_GPIO_QUEUE_PORT
    GPIO_PinModeSet(OPENREF_GPIO_QUEUE_PORT, OPENREF_GPIO_QUEUE_PIN, gpioModePushPull, 0);
#endif
#ifdef OPENREF_GPIO_START_PORT
    GPIO_PinModeSet(OPENREF_GPIO_START_PORT, OPENREF_GPIO_START_PIN, gpioModePushPull, 0);
#endif
#ifdef OPENREF_GPIO_DONE_PORT
    GPIO_PinModeSet(OPENREF_GPIO_DONE_PORT, OPENREF_GPIO_DONE_PIN, gpioModePushPull, 0);
#endif
}
#elif defined(OPENREF_APP_AUTOROLE)
static void openref_gpio_mark_build(void) {}
static void openref_gpio_mark_queue(void) {}
static void openref_gpio_mark_start(void) {}
static void openref_gpio_mark_done(void) {}
static void openref_gpio_init_markers(void) {}
#endif

void openref_app_init(void)
{
    uint8_t packet[OPENREF_PACKET_PAIR_MAX_PACKET_BYTES];

    openref_packet_pair_init_state(&app_state);
    uint16_t length = openref_packet_pair_build_ping(
        &app_state,
        OPENREF_PACKET_PAIR_TX_NODE_ID,
        OPENREF_PACKET_PAIR_RX_NODE_ID,
        0u,
        packet,
        sizeof(packet));

    printf("\r\n{{(openrefApp)}{Status:%s}{PacketBytes:%u}{Sequence:%u}}}\r\n",
           (length == openref_proto0_packet_length(OPENREF_PACKET_PAIR_PAYLOAD_BYTES)) ? "Linked" : "SelfTestFail",
           (unsigned int)length,
           (unsigned int)app_state.sequence);

    openref_packet_pair_init_state(&app_state);
}

void openref_app_process_action(void)
{
#ifdef OPENREF_APP_AUTOROLE
    if (openref_app_role != active_role) {
        active_role = openref_app_role;
        if (active_role != OPENREF_APP_ROLE_MEM_REPORT) {
            openref_packet_pair_init_state(&app_state);
        }
        autotx_configured = false;
        autorx_configured = false;
        schedtx_configured = false;
        schedtx_pending = false;
        schedtx_started_reported = false;
        schedtx_summary_reported = false;
        if (railHandle != NULL) {
            rxHeld = false;
            (void)RAIL_Idle(railHandle, RAIL_IDLE_ABORT, false);
        }
        printf("\r\n{{(openrefRole)}{Role:%u}}}\r\n", (unsigned int)active_role);
    }
#endif

#ifdef OPENREF_APP_AUTOROLE
    if (active_role == OPENREF_APP_ROLE_MEM_REPORT) {
        printf("\r\n{{(openrefMem)}{StateBytes:%u}{MaxPacketBytes:%u}{Rx:%u}{Gaps:%u}{Faults:%u}}}\r\n",
               (unsigned int)sizeof(app_state),
               (unsigned int)OPENREF_PACKET_PAIR_MAX_PACKET_BYTES,
               (unsigned int)app_state.rx_done_count,
               (unsigned int)app_state.rx_gap_count,
               (unsigned int)app_state.fault_count);
        openref_app_role = OPENREF_APP_ROLE_IDLE;
        return;
    }
#endif

#ifdef OPENREF_APP_AUTOROLE
    if (active_role == OPENREF_APP_ROLE_SCHEDULED_TX) {
    if (railHandle == NULL) {
        return;
    }

    if (!schedtx_configured) {
        uint16_t payload_bytes = openref_app_current_payload_bytes();
        uint16_t packet_bytes = openref_proto0_packet_length(payload_bytes);
        uint16_t fixed_length = RAIL_SetFixedLength(railHandle, packet_bytes);
        RAIL_ConfigEvents(
            railHandle,
            RAIL_EVENT_TX_STARTED | RAIL_EVENTS_TX_COMPLETION,
            RAIL_EVENT_TX_STARTED | RAIL_EVENTS_TX_COMPLETION);
        openref_gpio_init_markers();
        openref_packet_pair_init_state(&app_state);
        schedtx_attempt_count = 0u;
        schedtx_accept_count = 0u;
        schedtx_reject_count = 0u;
        schedtx_sequence = 0u;
        schedtx_pending = false;
        schedtx_started_reported = false;
        schedtx_summary_reported = false;
        schedtx_next_queue_us = RAIL_GetTime() + OPENREF_APP_SCHEDTX_LEAD_US;
        printf("\r\n{{(openrefSchedTx)}{Status:Configured}{FixedLength:%u}{PayloadBytes:%u}{LeadUs:%u}{IntervalUs:%u}{Attempts:%u}}}\r\n",
               (unsigned int)fixed_length,
               (unsigned int)payload_bytes,
               (unsigned int)OPENREF_APP_SCHEDTX_LEAD_US,
               (unsigned int)OPENREF_APP_SCHEDTX_INTERVAL_US,
               (unsigned int)openref_app_schedtx_attempts);
        schedtx_configured = true;
        return;
    }

    if (schedtx_pending) {
        if (!schedtx_started_reported &&
            counters.userTxStarted > schedtx_started_counter &&
            txStartTime != 0u) {
            int32_t launch_error_us = (int32_t)(txStartTime - schedtx_requested_tx_us);
            openref_gpio_mark_start();
            printf("\r\n{{(openrefSchedTx)}{Status:Started}{Sequence:%u}{RequestedUs:%u}{StartUs:%u}{LaunchErrorUs:%d}}}\r\n",
                   (unsigned int)schedtx_sequence,
                   (unsigned int)schedtx_requested_tx_us,
                   (unsigned int)txStartTime,
                   (int)launch_error_us);
            schedtx_started_reported = true;
        }

        if (counters.userTx > schedtx_done_counter) {
            openref_gpio_mark_done();
            printf("\r\n{{(openrefSchedTx)}{Status:Done}{Sequence:%u}{UserTx:%u}{UserTxStarted:%u}}}\r\n",
                   (unsigned int)schedtx_sequence,
                   (unsigned int)counters.userTx,
                   (unsigned int)counters.userTxStarted);
            schedtx_pending = false;
            schedtx_next_queue_us = RAIL_GetTime() + OPENREF_APP_SCHEDTX_INTERVAL_US;
        }
        return;
    }

    if (schedtx_attempt_count >= openref_app_schedtx_attempts) {
        if (!schedtx_summary_reported) {
            printf("\r\n{{(openrefSchedTx)}{Status:Summary}{Attempts:%u}{Accepted:%u}{Rejected:%u}{UserTx:%u}{UserTxStarted:%u}}}\r\n",
                   (unsigned int)schedtx_attempt_count,
                   (unsigned int)schedtx_accept_count,
                   (unsigned int)schedtx_reject_count,
                   (unsigned int)counters.userTx,
                   (unsigned int)counters.userTxStarted);
            schedtx_summary_reported = true;
        }
        return;
    }

    uint32_t now_us = RAIL_GetTime();
    if ((int32_t)(now_us - schedtx_next_queue_us) < 0) {
        return;
    }

    uint8_t packet[OPENREF_PACKET_PAIR_MAX_PACKET_BYTES];
    uint16_t payload_bytes = openref_app_current_payload_bytes();
    uint16_t length = openref_packet_pair_build_ping_with_payload(
        &app_state,
        OPENREF_PACKET_PAIR_TX_NODE_ID,
        OPENREF_PACKET_PAIR_RX_NODE_ID,
        now_us,
        payload_bytes,
        packet,
        sizeof(packet));
    if (length == 0u) {
        schedtx_reject_count++;
        app_state.fault_count++;
        schedtx_next_queue_us = now_us + OPENREF_APP_SCHEDTX_INTERVAL_US;
        return;
    }
    schedtx_sequence = app_state.sequence;
    openref_gpio_mark_build();

    uint16_t written = RAIL_WriteTxFifo(railHandle, packet, length, true);
    schedtx_requested_tx_us = RAIL_GetTime() + OPENREF_APP_SCHEDTX_LEAD_US;
    RAIL_ScheduleTxConfig_t config = {
        .when = schedtx_requested_tx_us,
        .mode = RAIL_TIME_ABSOLUTE,
        .txDuringRx = RAIL_SCHEDULED_TX_DURING_RX_POSTPONE_TX
    };
    openref_gpio_mark_queue();
    schedtx_started_counter = counters.userTxStarted;
    schedtx_done_counter = counters.userTx;
    txStartTime = 0u;
    RAIL_Status_t status = RAIL_STATUS_INVALID_PARAMETER;
    if (written == length) {
        status = RAIL_StartScheduledTx(
            railHandle,
            channel,
            RAIL_TX_OPTIONS_DEFAULT,
            &config,
            NULL);
    }

    schedtx_attempt_count++;
    if (written == length && status == RAIL_STATUS_NO_ERROR) {
        schedtx_accept_count++;
        schedtx_pending = true;
        schedtx_started_reported = false;
    } else {
        schedtx_reject_count++;
        schedtx_next_queue_us = now_us + OPENREF_APP_SCHEDTX_INTERVAL_US;
    }
    printf("\r\n{{(openrefSchedTx)}{Status:Queued}{Sequence:%u}{Attempt:%u}{RequestedUs:%u}{Length:%u}{Written:%u}{RailStatus:%u}}}\r\n",
           (unsigned int)schedtx_sequence,
           (unsigned int)schedtx_attempt_count,
           (unsigned int)schedtx_requested_tx_us,
           (unsigned int)length,
           (unsigned int)written,
           (unsigned int)status);
    }
#endif

#if defined(OPENREF_APP_AUTOTX) || defined(OPENREF_APP_AUTOROLE)
#ifdef OPENREF_APP_AUTOROLE
    if (active_role == OPENREF_APP_ROLE_TX)
#endif
    {
    if (railHandle == NULL) {
        return;
    }

    if (!autotx_configured) {
        uint16_t payload_bytes = openref_app_current_payload_bytes();
        uint16_t packet_bytes = openref_proto0_packet_length(payload_bytes);
        uint16_t fixed_length = RAIL_SetFixedLength(railHandle, packet_bytes);
        autotx_configured = true;
        next_autotx_us = RAIL_GetTime() + OPENREF_APP_AUTOTX_INTERVAL_US;
        printf("\r\n{{(openrefAutoTx)}{Status:Configured}{FixedLength:%u}{PayloadBytes:%u}{IntervalUs:%u}}}\r\n",
               (unsigned int)fixed_length,
               (unsigned int)payload_bytes,
               (unsigned int)OPENREF_APP_AUTOTX_INTERVAL_US);
        return;
    }

    uint32_t now_us = RAIL_GetTime();
    if ((int32_t)(now_us - next_autotx_us) < 0) {
        return;
    }

    uint8_t packet[OPENREF_PACKET_PAIR_MAX_PACKET_BYTES];
    uint16_t length = 0u;
#ifdef OPENREF_APP_AUTOROLE
    if (openref_app_payload_bytes <= OPENREF_PROTO0_MAX_PAYLOAD_BYTES) {
        length = openref_packet_pair_build_ping_with_payload(
            &app_state,
            OPENREF_PACKET_PAIR_TX_NODE_ID,
            OPENREF_PACKET_PAIR_RX_NODE_ID,
            now_us,
            (uint16_t)openref_app_payload_bytes,
            packet,
            sizeof(packet));
    }
#else
    length = openref_packet_pair_build_ping(
        &app_state,
        OPENREF_PACKET_PAIR_TX_NODE_ID,
        OPENREF_PACKET_PAIR_RX_NODE_ID,
        now_us,
        packet,
        sizeof(packet));
#endif
    if (length == 0u) {
        app_state.fault_count++;
        next_autotx_us = now_us + OPENREF_APP_AUTOTX_INTERVAL_US;
        return;
    }

    uint16_t written = RAIL_WriteTxFifo(railHandle, packet, length, true);
    RAIL_Status_t status = RAIL_STATUS_INVALID_STATE;
    if (written == length) {
        status = RAIL_StartTx(railHandle, channel, RAIL_TX_OPTIONS_DEFAULT, NULL);
    }

    printf("\r\n{{(openrefAutoTx)}{Sequence:%u}{Length:%u}{Written:%u}{Status:%u}}}\r\n",
           (unsigned int)app_state.sequence,
           (unsigned int)length,
           (unsigned int)written,
           (unsigned int)status);

    next_autotx_us = now_us + OPENREF_APP_AUTOTX_INTERVAL_US;
    }
#endif

#if defined(OPENREF_APP_AUTORX) || defined(OPENREF_APP_AUTOROLE)
#ifdef OPENREF_APP_AUTOROLE
    if (active_role == OPENREF_APP_ROLE_RX)
#endif
    {
    if (railHandle == NULL) {
        return;
    }

    if (!autorx_configured) {
        uint16_t payload_bytes = openref_app_current_payload_bytes();
        uint16_t packet_bytes = openref_proto0_packet_length(payload_bytes);
        uint16_t fixed_length = RAIL_SetFixedLength(railHandle, packet_bytes);
        rxHeld = true;
        RAIL_Status_t status = RAIL_StartRx(railHandle, channel, NULL);
        autorx_configured = true;
        printf("\r\n{{(openrefAutoRx)}{Status:Configured}{FixedLength:%u}{PayloadBytes:%u}{StartRx:%u}}}\r\n",
               (unsigned int)fixed_length,
               (unsigned int)payload_bytes,
               (unsigned int)status);
        return;
    }

    while (packetsHeld > 0u) {
        RAIL_RxPacketInfo_t packet_info;
        RAIL_RxPacketHandle_t packet_handle = RAIL_GetRxPacketInfo(
            railHandle,
            RAIL_RX_PACKET_HANDLE_OLDEST_COMPLETE,
            &packet_info);
        if (packet_handle == RAIL_RX_PACKET_HANDLE_INVALID) {
            return;
        }

        uint8_t packet[OPENREF_PACKET_PAIR_MAX_PACKET_BYTES];
        uint16_t length = packet_info.packetBytes;
        bool parsed = false;
        bool gap_detected = false;
        uint16_t expected_sequence = 0u;
        openref_proto0_packet_header_t header;

        if (packet_info.packetStatus == RAIL_RX_PACKET_READY_SUCCESS &&
            length <= sizeof(packet)) {
            RAIL_CopyRxPacket(packet, &packet_info);
            parsed = openref_packet_pair_parse_rx(
                &app_state,
                packet,
                length,
                &header,
                &gap_detected,
                &expected_sequence);
        } else {
            app_state.fault_count++;
        }

        (void)RAIL_ReleaseRxPacket(railHandle, packet_handle);
        if (packetsHeld > 0u) {
            packetsHeld--;
        }

        if (!parsed) {
            printf("\r\n{{(openrefAutoRx)}{Status:ParseFail}{Length:%u}{Faults:%u}}}\r\n",
                   (unsigned int)length,
                   (unsigned int)app_state.fault_count);
            continue;
        }

        if (gap_detected ||
            (app_state.rx_done_count % OPENREF_APP_AUTORX_REPORT_EVERY) == 0u) {
            printf("\r\n{{(openrefAutoRx)}{Rx:%u}{Sequence:%u}{Gaps:%u}{Faults:%u}{Gap:%u}{Expected:%u}}}\r\n",
                   (unsigned int)app_state.rx_done_count,
                   (unsigned int)header.sequence,
                   (unsigned int)app_state.rx_gap_count,
                   (unsigned int)app_state.fault_count,
                   gap_detected ? 1u : 0u,
                   (unsigned int)expected_sequence);
        }
    }
    }
#endif
}
