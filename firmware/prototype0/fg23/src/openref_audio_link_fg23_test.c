#include <assert.h>
#include <string.h>

#include "openref_audio_link_fg23.h"

typedef struct {
    uint32_t now_us;
    uint32_t starts;
    uint32_t aborts;
    uint32_t reset_asserts;
    uint32_t reset_releases;
    bool request;
    bool fail_start;
    bool fail_abort;
    bool fail_reset;
    bool complete_during_start;
    openref_audio_fg23_t *adapter;
    uint8_t last_tx[OPENREF_AUDIO_LINK_FRAME_BYTES];
    uint8_t *active_rx;
} fake_hal_t;

static bool start_transfer(void *context, const uint8_t *tx, uint8_t *rx,
                           uint16_t length)
{
    fake_hal_t *hal = context;
    assert(length == OPENREF_AUDIO_LINK_FRAME_BYTES);
    hal->starts++;
    memcpy(hal->last_tx, tx, length);
    hal->active_rx = rx;
    if (hal->complete_during_start) {
        openref_audio_link_frame_t status = {
            .kind = OPENREF_AUDIO_LINK_STATUS,
        };
        assert(openref_audio_link_encode(
            &status, rx, OPENREF_AUDIO_LINK_FRAME_BYTES));
        assert(openref_audio_fg23_transfer_complete_isr(hal->adapter, true));
    }
    return !hal->fail_start;
}

static bool abort_transfer(void *context)
{
    fake_hal_t *hal = context;
    hal->aborts++;
    return !hal->fail_abort;
}

static bool request_asserted(void *context)
{
    return ((fake_hal_t *)context)->request;
}

static bool set_reset(void *context, bool asserted)
{
    fake_hal_t *hal = context;
    if (asserted) {
        hal->reset_asserts++;
    } else {
        hal->reset_releases++;
    }
    return !hal->fail_reset;
}

static uint32_t clock_us(void *context)
{
    return ((fake_hal_t *)context)->now_us;
}

static openref_audio_fg23_hooks_t hooks(fake_hal_t *hal)
{
    openref_audio_fg23_hooks_t result = {
        start_transfer, abort_transfer, request_asserted, set_reset,
        clock_us, hal,
    };
    return result;
}

static openref_audio_fg23_t initialized(fake_hal_t *hal)
{
    openref_audio_fg23_t adapter;
    openref_audio_fg23_config_t config = {100u, 500u};
    assert(openref_audio_fg23_init(&adapter, &config, hooks(hal)));
    hal->adapter = &adapter;
    assert(adapter.reset_asserted && hal->reset_asserts == 1u);
    hal->now_us = 100u;
    assert(openref_audio_fg23_process(&adapter));
    assert(!adapter.reset_asserted && hal->reset_releases == 1u);
    return adapter;
}

static openref_audio_link_frame_t audio_frame(uint16_t sequence)
{
    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_LOCAL_AUDIO,
        .source_id = 1u,
        .flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                 OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID,
        .sequence = sequence,
    };
    return frame;
}

static void complete_with_status(openref_audio_fg23_t *adapter, fake_hal_t *hal)
{
    openref_audio_link_frame_t status = {.kind = OPENREF_AUDIO_LINK_STATUS};
    assert(openref_audio_link_encode(
        &status, hal->active_rx, OPENREF_AUDIO_LINK_FRAME_BYTES));
    assert(openref_audio_fg23_transfer_complete_isr(adapter, true));
    assert(openref_audio_fg23_process(adapter));
}

static void test_local_queue_full_duplex_completion(void)
{
    fake_hal_t hal = {0};
    openref_audio_fg23_t adapter = initialized(&hal);
    openref_audio_link_frame_t frame = audio_frame(7u);
    assert(openref_audio_fg23_queue(&adapter, &frame));
    assert(openref_audio_fg23_process(&adapter));
    assert(adapter.transfer_active && hal.starts == 1u);
    openref_audio_link_frame_t decoded;
    assert(openref_audio_link_decode(
        hal.last_tx, sizeof(hal.last_tx), &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_LOCAL_AUDIO);
    assert(decoded.sequence == 7u);
    complete_with_status(&adapter, &hal);
    assert(adapter.transfers_completed == 1u);
    assert(adapter.transport.status_received == 1u);
}

static void test_peer_request_starts_valid_idle_transaction(void)
{
    fake_hal_t hal = {.request = true};
    openref_audio_fg23_t adapter = initialized(&hal);
    assert(openref_audio_fg23_process(&adapter));
    openref_audio_link_frame_t decoded;
    assert(openref_audio_link_decode(
        hal.last_tx, sizeof(hal.last_tx), &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_STATUS);
    assert(adapter.transport.idle_transactions == 1u);
}

static void test_start_failure_retries_identical_prepared_frame(void)
{
    fake_hal_t hal = {.fail_start = true};
    openref_audio_fg23_t adapter = initialized(&hal);
    openref_audio_link_frame_t frame = audio_frame(9u);
    assert(openref_audio_fg23_queue(&adapter, &frame));
    assert(!openref_audio_fg23_process(&adapter));
    uint8_t first[OPENREF_AUDIO_LINK_FRAME_BYTES];
    memcpy(first, hal.last_tx, sizeof(first));
    assert(adapter.tx_prepared && !adapter.transfer_active);
    hal.fail_start = false;
    assert(openref_audio_fg23_process(&adapter));
    assert(memcmp(first, hal.last_tx, sizeof(first)) == 0);
    assert(hal.starts == 2u && adapter.start_failures == 1u);
}

static void test_timeout_aborts_and_resets_peer(void)
{
    fake_hal_t hal = {.request = true};
    openref_audio_fg23_t adapter = initialized(&hal);
    assert(openref_audio_fg23_process(&adapter));
    hal.now_us += 501u;
    assert(openref_audio_fg23_process(&adapter));
    assert(adapter.transfer_timeouts == 1u);
    assert(adapter.transfer_failures == 1u);
    assert(hal.aborts == 1u && hal.reset_asserts == 2u);
    assert(adapter.reset_asserted && !adapter.transfer_active);
    assert(!openref_audio_fg23_transfer_complete_isr(&adapter, true));
    assert(adapter.unexpected_completions == 1u);
}

static void test_completion_failure_is_deferred_to_main_loop(void)
{
    fake_hal_t hal = {.request = true};
    openref_audio_fg23_t adapter = initialized(&hal);
    assert(openref_audio_fg23_process(&adapter));
    assert(openref_audio_fg23_transfer_complete_isr(&adapter, false));
    assert(adapter.transfer_failures == 0u);
    assert(!openref_audio_fg23_process(&adapter));
    assert(adapter.transfer_failures == 1u && !adapter.transfer_active);
}

static void test_completion_may_preempt_start_transfer_return(void)
{
    fake_hal_t hal = {.request = true, .complete_during_start = true};
    openref_audio_fg23_t adapter = initialized(&hal);
    /* initialized() returns the adapter by value, so refresh the fake pointer. */
    hal.adapter = &adapter;
    assert(openref_audio_fg23_process(&adapter));
    assert(adapter.transfer_active && adapter.completion_pending);
    hal.request = false;
    assert(openref_audio_fg23_process(&adapter));
    assert(!adapter.transfer_active && !adapter.completion_pending);
    assert(adapter.transfers_completed == 1u);
}

static void test_invalid_configuration_fails_closed(void)
{
    fake_hal_t hal = {0};
    openref_audio_fg23_t adapter;
    openref_audio_fg23_config_t config = {100u, 0u};
    assert(!openref_audio_fg23_init(&adapter, &config, hooks(&hal)));
    assert(!adapter.initialized);
    assert(!openref_audio_fg23_process(&adapter));
}

int main(void)
{
    test_local_queue_full_duplex_completion();
    test_peer_request_starts_valid_idle_transaction();
    test_start_failure_retries_identical_prepared_frame();
    test_timeout_aborts_and_resets_peer();
    test_completion_failure_is_deferred_to_main_loop();
    test_completion_may_preempt_start_transfer_return();
    test_invalid_configuration_fails_closed();
    return 0;
}
