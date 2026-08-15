#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "openref_secure_network_packet.h"

static uint8_t checksum(
    const uint8_t *nonce, const uint8_t *aad, const uint8_t *ciphertext)
{
    uint8_t value = 0u;
    for (uint8_t i = 0u; i < OPENREF_SECURITY_NONCE_BYTES; i++) value ^= nonce[i];
    for (uint8_t i = 0u; i < OPENREF_SECURITY_AAD_BYTES; i++) value ^= aad[i];
    for (uint8_t i = 0u; i < OPENREF_SECURITY_PLAINTEXT_BYTES; i++) value ^= ciphertext[i];
    return value;
}

static bool encrypt_probe(
    void *context, const uint8_t *nonce, const uint8_t *aad,
    const uint8_t *plaintext, uint8_t *ciphertext, uint8_t *tag)
{
    (void)context;
    for (uint8_t i = 0u; i < OPENREF_SECURITY_PLAINTEXT_BYTES; i++) {
        ciphertext[i] = plaintext[i] ^ nonce[i % OPENREF_SECURITY_NONCE_BYTES];
    }
    memset(tag, checksum(nonce, aad, ciphertext), OPENREF_SECURITY_TAG_BYTES);
    return true;
}

static bool decrypt_probe(
    void *context, const uint8_t *nonce, const uint8_t *aad,
    const uint8_t *ciphertext, const uint8_t *tag, uint8_t *plaintext)
{
    (void)context;
    uint8_t expected = checksum(nonce, aad, ciphertext);
    for (uint8_t i = 0u; i < OPENREF_SECURITY_TAG_BYTES; i++) {
        if (tag[i] != expected) return false;
    }
    for (uint8_t i = 0u; i < OPENREF_SECURITY_PLAINTEXT_BYTES; i++) {
        plaintext[i] = ciphertext[i] ^ nonce[i % OPENREF_SECURITY_NONCE_BYTES];
    }
    return true;
}

int main(void)
{
    uint8_t original[OPENREF_NETWORK_PACKET_BYTES];
    assert(openref_network_build_audio_packet(2u, 7u, 9000u, original,
                                              sizeof(original)) == sizeof(original));
    uint8_t secured[OPENREF_SECURE_NETWORK_PACKET_BYTES];
    assert(openref_secure_network_wrap(
        encrypt_probe, NULL, 33u, 4u, 10u, original, secured));
    openref_proto0_packet_header_t header;
    assert(openref_proto0_decode_header(secured, sizeof(secured), &header));
    assert(header.payload_length == OPENREF_SECURITY_ENVELOPE_BYTES);

    openref_security_replay_state_t replay[6] = {0};
    uint8_t opened[OPENREF_NETWORK_PACKET_BYTES];
    openref_security_replay_result_t result;
    assert(openref_secure_network_open(
        decrypt_probe, NULL, 33u, replay, secured, opened, &result));
    assert(result == OPENREF_SECURITY_REPLAY_ACCEPT_FIRST);
    assert(memcmp(original, opened, sizeof(original)) == 0);
    assert(!openref_secure_network_open(
        decrypt_probe, NULL, 33u, replay, secured, opened, &result));
    assert(result == OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE);

    assert(openref_secure_network_wrap(
        encrypt_probe, NULL, 33u, 4u, 11u, original, secured));
    secured[OPENREF_SECURE_NETWORK_PACKET_BYTES - 1u] ^= 1u;
    assert(!openref_secure_network_open(
        decrypt_probe, NULL, 33u, replay, secured, opened, &result));
    secured[OPENREF_SECURE_NETWORK_PACKET_BYTES - 1u] ^= 1u;
    assert(openref_secure_network_open(
        decrypt_probe, NULL, 33u, replay, secured, opened, &result));
    assert(result == OPENREF_SECURITY_REPLAY_ACCEPT_NEW);
    return 0;
}
