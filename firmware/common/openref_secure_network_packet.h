#ifndef OPENREF_SECURE_NETWORK_PACKET_H
#define OPENREF_SECURE_NETWORK_PACKET_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_network_packet.h"
#include "openref_security.h"

#define OPENREF_SECURE_NETWORK_PACKET_BYTES \
    (OPENREF_PROTO0_HEADER_BYTES + OPENREF_SECURITY_ENVELOPE_BYTES)

bool openref_secure_network_wrap(
    openref_security_ccm_encrypt_fn encrypt,
    void *context,
    uint32_t crew_session_id,
    uint32_t boot_counter,
    uint32_t packet_counter,
    const uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES]);

bool openref_secure_network_open(
    openref_security_ccm_decrypt_fn decrypt,
    void *context,
    uint32_t crew_session_id,
    openref_security_replay_state_t replay_by_source[6],
    const uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES],
    uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    openref_security_replay_result_t *replay_result);

#endif
