#include <assert.h>
#include <stdint.h>

#include "openref_peer_supervisor.h"

int main(void)
{
    const openref_peer_config_t config = {
        .heartbeat_timeout_ms = 100u,
        .reset_hold_ms = 10u,
        .boot_wait_ms = 50u,
        .power_cycle_wait_ms = 100u,
        .maximum_reset_attempts = 2u,
    };
    openref_peer_supervisor_t supervisor;
    assert(openref_peer_supervisor_init(&supervisor, &config, 0u));
    assert(openref_peer_supervisor_tick(&supervisor, 100u) == 0u);
    assert((openref_peer_supervisor_tick(&supervisor, 101u) &
            OPENREF_PEER_ACTION_ASSERT_RESET) != 0u);
    assert(openref_peer_supervisor_tick(&supervisor, 110u) ==
           OPENREF_PEER_ACTION_MUTE_AUDIO);
    assert((openref_peer_supervisor_tick(&supervisor, 111u) &
            OPENREF_PEER_ACTION_RELEASE_RESET) != 0u);
    assert((openref_peer_supervisor_tick(&supervisor, 161u) &
            OPENREF_PEER_ACTION_ASSERT_RESET) != 0u);
    assert((openref_peer_supervisor_tick(&supervisor, 171u) &
            OPENREF_PEER_ACTION_RELEASE_RESET) != 0u);
    assert((openref_peer_supervisor_tick(&supervisor, 221u) &
            OPENREF_PEER_ACTION_POWER_CYCLE) != 0u);
    assert((openref_peer_supervisor_tick(&supervisor, 321u) &
            OPENREF_PEER_ACTION_REPORT_FAULT) != 0u);
    assert(supervisor.state == OPENREF_PEER_FAILED);

    openref_peer_supervisor_heartbeat(&supervisor, 330u);
    assert(supervisor.state == OPENREF_PEER_HEALTHY);
    assert(supervisor.recovery_count == 1u);
    assert(supervisor.reset_attempts == 0u);
    return 0;
}
