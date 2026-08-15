#ifndef OPENREF_SECURE_TRANSPORT_H
#define OPENREF_SECURE_TRANSPORT_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_secure_network_packet.h"

typedef struct {
    openref_security_ccm_encrypt_fn encrypt;
    openref_security_ccm_decrypt_fn decrypt;
    void *crypto_context;
    uint32_t crew_session_id;
    uint32_t boot_counter;
    uint32_t next_packet_counter;
    openref_security_replay_state_t replay_by_source[6];
    uint32_t protected_packets;
    uint32_t opened_packets;
    uint32_t protect_failures;
    uint32_t open_failures;
    uint32_t replay_rejections;
    bool transmit_exhausted;
    bool initialized;
} openref_secure_transport_t;

bool openref_secure_transport_init(
    openref_secure_transport_t *transport,
    openref_security_ccm_encrypt_fn encrypt,
    openref_security_ccm_decrypt_fn decrypt,
    void *crypto_context,
    uint32_t crew_session_id,
    uint32_t boot_counter,
    uint32_t initial_packet_counter);

bool openref_secure_transport_protect(
    openref_secure_transport_t *transport,
    const uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES]);

bool openref_secure_transport_open(
    openref_secure_transport_t *transport,
    const uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES],
    uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    openref_security_replay_result_t *replay_result);

#endif
