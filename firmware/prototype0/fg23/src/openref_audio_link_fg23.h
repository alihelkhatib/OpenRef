#ifndef OPENREF_AUDIO_LINK_FG23_H
#define OPENREF_AUDIO_LINK_FG23_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_transport.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef bool (*openref_audio_fg23_start_transfer_fn)(
    void *context,
    const uint8_t tx[OPENREF_AUDIO_LINK_FRAME_BYTES],
    uint8_t rx[OPENREF_AUDIO_LINK_FRAME_BYTES],
    uint16_t length);

typedef bool (*openref_audio_fg23_abort_transfer_fn)(void *context);
typedef bool (*openref_audio_fg23_request_asserted_fn)(void *context);
typedef bool (*openref_audio_fg23_set_reset_fn)(void *context, bool asserted);
typedef uint32_t (*openref_audio_fg23_clock_us_fn)(void *context);

typedef struct {
    openref_audio_fg23_start_transfer_fn start_transfer;
    openref_audio_fg23_abort_transfer_fn abort_transfer;
    openref_audio_fg23_request_asserted_fn request_asserted;
    openref_audio_fg23_set_reset_fn set_peer_reset;
    openref_audio_fg23_clock_us_fn clock_us;
    void *context;
} openref_audio_fg23_hooks_t;

typedef struct {
    uint32_t reset_hold_us;
    uint32_t transfer_timeout_us;
} openref_audio_fg23_config_t;

typedef struct {
    openref_audio_transport_t transport;
    openref_audio_fg23_hooks_t hooks;
    openref_audio_fg23_config_t config;
    uint8_t tx_wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    uint8_t rx_wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    uint32_t reset_started_us;
    uint32_t transfer_started_us;
    uint32_t transfers_started;
    uint32_t transfers_completed;
    uint32_t start_failures;
    uint32_t transfer_failures;
    uint32_t transfer_timeouts;
    uint32_t abort_failures;
    uint32_t reset_count;
    uint32_t reset_failures;
    uint32_t unexpected_completions;
    volatile bool completion_pending;
    volatile bool completion_success;
    bool initialized;
    bool reset_asserted;
    bool transfer_active;
    bool tx_prepared;
} openref_audio_fg23_t;

bool openref_audio_fg23_init(
    openref_audio_fg23_t *adapter,
    const openref_audio_fg23_config_t *config,
    openref_audio_fg23_hooks_t hooks);

bool openref_audio_fg23_queue(
    openref_audio_fg23_t *adapter,
    const openref_audio_link_frame_t *frame);

/* Call from the main loop; codec and frame parsing never run in the DMA ISR. */
bool openref_audio_fg23_process(openref_audio_fg23_t *adapter);

/* Call once from the SPI/LDMA completion ISR. */
bool openref_audio_fg23_transfer_complete_isr(
    openref_audio_fg23_t *adapter,
    bool success);

/* Assert peer reset now, aborting an active transfer if necessary. */
bool openref_audio_fg23_reset_peer(openref_audio_fg23_t *adapter);

#ifdef __cplusplus
}
#endif

#endif
