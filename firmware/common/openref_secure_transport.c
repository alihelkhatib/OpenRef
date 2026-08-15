#include "openref_secure_transport.h"

#include <stddef.h>
#include <string.h>

bool openref_secure_transport_init(
    openref_secure_transport_t *transport,
    openref_security_ccm_encrypt_fn encrypt,
    openref_security_ccm_decrypt_fn decrypt,
    void *crypto_context,
    uint32_t crew_session_id,
    uint32_t boot_counter,
    uint32_t initial_packet_counter)
{
    if (transport == NULL || encrypt == NULL || decrypt == NULL ||
        crew_session_id == 0u || boot_counter == 0u ||
        initial_packet_counter == 0u) {
        return false;
    }
    memset(transport, 0, sizeof(*transport));
    transport->encrypt = encrypt;
    transport->decrypt = decrypt;
    transport->crypto_context = crypto_context;
    transport->crew_session_id = crew_session_id;
    transport->boot_counter = boot_counter;
    transport->next_packet_counter = initial_packet_counter;
    transport->initialized = true;
    return true;
}

bool openref_secure_transport_protect(
    openref_secure_transport_t *transport,
    const uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES])
{
    if (transport == NULL || !transport->initialized ||
        transport->transmit_exhausted || plaintext_packet == NULL ||
        secured_packet == NULL) {
        if (transport != NULL && transport->initialized) {
            transport->protect_failures++;
        }
        return false;
    }
    uint32_t counter = transport->next_packet_counter;
    if (!openref_secure_network_wrap(transport->encrypt,
            transport->crypto_context, transport->crew_session_id,
            transport->boot_counter, counter, plaintext_packet,
            secured_packet)) {
        transport->protect_failures++;
        return false;
    }
    transport->protected_packets++;
    if (counter == UINT32_MAX) {
        transport->transmit_exhausted = true;
    } else {
        transport->next_packet_counter++;
    }
    return true;
}

bool openref_secure_transport_open(
    openref_secure_transport_t *transport,
    const uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES],
    uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    openref_security_replay_result_t *replay_result)
{
    if (transport == NULL || !transport->initialized ||
        secured_packet == NULL || plaintext_packet == NULL ||
        replay_result == NULL) {
        if (transport != NULL && transport->initialized) {
            transport->open_failures++;
        }
        return false;
    }
    *replay_result = OPENREF_SECURITY_REPLAY_ACCEPT_FIRST;
    if (!openref_secure_network_open(transport->decrypt,
            transport->crypto_context, transport->crew_session_id,
            transport->replay_by_source, secured_packet, plaintext_packet,
            replay_result)) {
        transport->open_failures++;
        if (*replay_result == OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE ||
            *replay_result == OPENREF_SECURITY_REPLAY_REJECT_STALE ||
            *replay_result == OPENREF_SECURITY_REPLAY_REJECT_OLD_BOOT) {
            transport->replay_rejections++;
        }
        return false;
    }
    transport->opened_packets++;
    return true;
}
