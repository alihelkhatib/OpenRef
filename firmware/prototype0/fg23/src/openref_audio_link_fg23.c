#include "openref_audio_link_fg23.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static void increment_saturating(uint32_t *value)
{
    if (*value != UINT32_MAX) {
        (*value)++;
    }
}

static bool assert_reset(openref_audio_fg23_t *adapter)
{
    bool ok = true;
    if (adapter->transfer_active) {
        if (!adapter->hooks.abort_transfer(adapter->hooks.context)) {
            increment_saturating(&adapter->abort_failures);
            ok = false;
        }
        adapter->transfer_active = false;
        adapter->completion_pending = false;
    }
    if (!adapter->hooks.set_peer_reset(adapter->hooks.context, true)) {
        increment_saturating(&adapter->reset_failures);
        return false;
    }
    adapter->reset_asserted = true;
    adapter->reset_started_us = adapter->hooks.clock_us(adapter->hooks.context);
    increment_saturating(&adapter->reset_count);
    return ok;
}

bool openref_audio_fg23_init(
    openref_audio_fg23_t *adapter,
    const openref_audio_fg23_config_t *config,
    openref_audio_fg23_hooks_t hooks)
{
    if (adapter == NULL) {
        return false;
    }
    memset(adapter, 0, sizeof(*adapter));
    if (config == NULL || config->reset_hold_us == 0u ||
        config->transfer_timeout_us == 0u || hooks.start_transfer == NULL ||
        hooks.abort_transfer == NULL || hooks.request_asserted == NULL ||
        hooks.set_peer_reset == NULL || hooks.clock_us == NULL) {
        return false;
    }
    adapter->hooks = hooks;
    adapter->config = *config;
    openref_audio_transport_init(&adapter->transport);
    if (!assert_reset(adapter)) {
        return false;
    }
    adapter->initialized = true;
    return true;
}

bool openref_audio_fg23_queue(
    openref_audio_fg23_t *adapter,
    const openref_audio_link_frame_t *frame)
{
    return adapter != NULL && adapter->initialized &&
        openref_audio_transport_queue(&adapter->transport, frame);
}

bool openref_audio_fg23_transfer_complete_isr(
    openref_audio_fg23_t *adapter,
    bool success)
{
    if (adapter == NULL || !adapter->initialized ||
        !adapter->transfer_active || adapter->completion_pending) {
        if (adapter != NULL && adapter->initialized) {
            increment_saturating(&adapter->unexpected_completions);
        }
        return false;
    }
    adapter->completion_success = success;
    adapter->completion_pending = true;
    return true;
}

bool openref_audio_fg23_reset_peer(openref_audio_fg23_t *adapter)
{
    return adapter != NULL && adapter->initialized && assert_reset(adapter);
}

bool openref_audio_fg23_process(openref_audio_fg23_t *adapter)
{
    if (adapter == NULL || !adapter->initialized) {
        return false;
    }
    uint32_t now_us = adapter->hooks.clock_us(adapter->hooks.context);
    if (adapter->reset_asserted) {
        if ((uint32_t)(now_us - adapter->reset_started_us) <
            adapter->config.reset_hold_us) {
            return true;
        }
        if (!adapter->hooks.set_peer_reset(adapter->hooks.context, false)) {
            increment_saturating(&adapter->reset_failures);
            return false;
        }
        adapter->reset_asserted = false;
        return true;
    }

    if (adapter->completion_pending) {
        bool success = adapter->completion_success;
        adapter->completion_pending = false;
        adapter->transfer_active = false;
        if (!success) {
            increment_saturating(&adapter->transfer_failures);
            return false;
        }
        increment_saturating(&adapter->transfers_completed);
        if (!openref_audio_transport_accept_rx(
                &adapter->transport, adapter->rx_wire)) {
            return false;
        }
        return true;
    }

    if (adapter->transfer_active) {
        if ((uint32_t)(now_us - adapter->transfer_started_us) <=
            adapter->config.transfer_timeout_us) {
            return true;
        }
        increment_saturating(&adapter->transfer_timeouts);
        increment_saturating(&adapter->transfer_failures);
        return assert_reset(adapter);
    }

    if (!adapter->tx_prepared) {
        bool local_request = openref_audio_transport_request_asserted(
            &adapter->transport);
        if (!local_request &&
            !adapter->hooks.request_asserted(adapter->hooks.context)) {
            return true;
        }
        if (!openref_audio_transport_prepare_tx(
                &adapter->transport, now_us, adapter->tx_wire)) {
            return false;
        }
        adapter->tx_prepared = true;
    }

    memset(adapter->rx_wire, 0, sizeof(adapter->rx_wire));
    /* Publish active state before enabling DMA; completion may preempt start. */
    adapter->transfer_active = true;
    adapter->transfer_started_us = now_us;
    if (!adapter->hooks.start_transfer(
            adapter->hooks.context, adapter->tx_wire, adapter->rx_wire,
            OPENREF_AUDIO_LINK_FRAME_BYTES)) {
        adapter->transfer_active = false;
        adapter->completion_pending = false;
        increment_saturating(&adapter->start_failures);
        return false;
    }
    adapter->tx_prepared = false;
    increment_saturating(&adapter->transfers_started);
    return true;
}
