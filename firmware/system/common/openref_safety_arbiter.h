#ifndef OPENREF_SAFETY_ARBITER_H
#define OPENREF_SAFETY_ARBITER_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_INHIBIT_POWER (1u << 0)
#define OPENREF_INHIBIT_STARTUP (1u << 1)
#define OPENREF_INHIBIT_ACCESSORY (1u << 2)
#define OPENREF_INHIBIT_PEER (1u << 3)
#define OPENREF_INHIBIT_WATCHDOG (1u << 4)
#define OPENREF_INHIBIT_UPDATE (1u << 5)
#define OPENREF_INHIBIT_SERVICE (1u << 6)
#define OPENREF_INHIBIT_USER (1u << 7)
#define OPENREF_INHIBIT_SYSTEM_FAULT (1u << 8)

typedef struct {
    uint32_t power_actions;
    uint32_t startup_actions;
    bool accessory_mute_transmit;
    bool accessory_mute_playback;
    uint32_t peer_actions;
    bool watchdog_healthy;
    bool update_active;
    bool privileged_service_active;
    bool user_transmit_mute;
    bool user_playback_mute;
    bool system_fault;
} openref_safety_inputs_t;

typedef struct {
    uint32_t transmit_mute_reasons;
    uint32_t playback_mute_reasons;
    uint32_t radio_inhibit_reasons;
    bool voice_uplink_enabled;
    bool playback_enabled;
    bool network_control_tx_enabled;
} openref_safety_output_t;

openref_safety_output_t openref_safety_arbitrate(
    const openref_safety_inputs_t *inputs);

#endif
