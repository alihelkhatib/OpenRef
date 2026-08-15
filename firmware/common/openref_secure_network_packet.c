#include "openref_secure_network_packet.h"

#include <stddef.h>

bool openref_secure_network_wrap(
    openref_security_ccm_encrypt_fn encrypt,
    void *context,
    uint32_t crew_session_id,
    uint32_t boot_counter,
    uint32_t packet_counter,
    const uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES])
{
    openref_proto0_packet_header_t header;
    if (encrypt == NULL || plaintext_packet == NULL || secured_packet == NULL ||
        !openref_network_parse_packet(
            plaintext_packet, OPENREF_NETWORK_PACKET_BYTES, &header)) {
        return false;
    }
    header.payload_length = OPENREF_SECURITY_ENVELOPE_BYTES;
    if (!openref_proto0_encode_header(
            &header, secured_packet, OPENREF_SECURE_NETWORK_PACKET_BYTES)) {
        return false;
    }
    return openref_security_protect(
        encrypt, context, crew_session_id, header.source_id, boot_counter,
        packet_counter, secured_packet,
        &plaintext_packet[OPENREF_PROTO0_HEADER_BYTES],
        &secured_packet[OPENREF_PROTO0_HEADER_BYTES]);
}

bool openref_secure_network_open(
    openref_security_ccm_decrypt_fn decrypt,
    void *context,
    uint32_t crew_session_id,
    openref_security_replay_state_t replay_by_source[6],
    const uint8_t secured_packet[OPENREF_SECURE_NETWORK_PACKET_BYTES],
    uint8_t plaintext_packet[OPENREF_NETWORK_PACKET_BYTES],
    openref_security_replay_result_t *replay_result)
{
    openref_proto0_packet_header_t header;
    if (decrypt == NULL || replay_by_source == NULL || secured_packet == NULL ||
        plaintext_packet == NULL || replay_result == NULL ||
        !openref_proto0_decode_header(
            secured_packet, OPENREF_SECURE_NETWORK_PACKET_BYTES, &header) ||
        header.source_id < 1u || header.source_id > 6u ||
        header.destination_id != 0u ||
        header.payload_length != OPENREF_SECURITY_ENVELOPE_BYTES ||
        (header.kind != OPENREF_PROTO0_PACKET_AUDIO_FRAME &&
         header.kind != OPENREF_PROTO0_PACKET_HEARTBEAT &&
         header.kind != OPENREF_PROTO0_PACKET_CONTROL)) {
        return false;
    }

    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES];
    if (!openref_security_open(
            decrypt, context, crew_session_id, header.source_id,
            secured_packet, &secured_packet[OPENREF_PROTO0_HEADER_BYTES],
            &replay_by_source[header.source_id - 1u], plaintext,
            replay_result)) {
        return false;
    }
    header.payload_length = OPENREF_NETWORK_PAYLOAD_BYTES;
    if (!openref_proto0_encode_header(
            &header, plaintext_packet, OPENREF_NETWORK_PACKET_BYTES)) {
        return false;
    }
    for (uint8_t index = 0u; index < OPENREF_NETWORK_PAYLOAD_BYTES; index++) {
        plaintext_packet[OPENREF_PROTO0_HEADER_BYTES + index] = plaintext[index];
    }
    return true;
}
