#include <assert.h>
#include <string.h>

#include "openref_secure_transport.h"

static uint8_t checksum(const uint8_t *nonce, const uint8_t *aad,
    const uint8_t *ciphertext)
{
    uint8_t value = 0u;
    for (uint8_t i = 0u; i < OPENREF_SECURITY_NONCE_BYTES; i++) value ^= nonce[i];
    for (uint8_t i = 0u; i < OPENREF_SECURITY_AAD_BYTES; i++) value ^= aad[i];
    for (uint8_t i = 0u; i < OPENREF_SECURITY_PLAINTEXT_BYTES; i++) value ^= ciphertext[i];
    return value;
}

static bool encrypt(void *context, const uint8_t *nonce, const uint8_t *aad,
    const uint8_t *plaintext, uint8_t *ciphertext, uint8_t *tag)
{
    (void)context;
    for (uint8_t i = 0u; i < OPENREF_SECURITY_PLAINTEXT_BYTES; i++)
        ciphertext[i] = plaintext[i] ^ nonce[i % OPENREF_SECURITY_NONCE_BYTES];
    memset(tag, checksum(nonce, aad, ciphertext), OPENREF_SECURITY_TAG_BYTES);
    return true;
}

static bool decrypt(void *context, const uint8_t *nonce, const uint8_t *aad,
    const uint8_t *ciphertext, const uint8_t *tag, uint8_t *plaintext)
{
    (void)context;
    uint8_t expected = checksum(nonce, aad, ciphertext);
    for (uint8_t i = 0u; i < OPENREF_SECURITY_TAG_BYTES; i++)
        if (tag[i] != expected) return false;
    for (uint8_t i = 0u; i < OPENREF_SECURITY_PLAINTEXT_BYTES; i++)
        plaintext[i] = ciphertext[i] ^ nonce[i % OPENREF_SECURITY_NONCE_BYTES];
    return true;
}

int main(void)
{
    openref_secure_transport_t sender;
    openref_secure_transport_t receiver;
    assert(openref_secure_transport_init(
        &sender, encrypt, decrypt, NULL, 7u, 2u, 1u));
    assert(openref_secure_transport_init(
        &receiver, encrypt, decrypt, NULL, 7u, 9u, 1u));
    uint8_t plain[OPENREF_NETWORK_PACKET_BYTES];
    assert(openref_network_build_audio_packet(
        1u, 5u, 100u, plain, sizeof(plain)) == sizeof(plain));
    uint8_t secured[OPENREF_SECURE_NETWORK_PACKET_BYTES];
    assert(openref_secure_transport_protect(&sender, plain, secured));
    assert(sender.next_packet_counter == 2u && sender.protected_packets == 1u);
    uint8_t opened[OPENREF_NETWORK_PACKET_BYTES];
    openref_security_replay_result_t result;
    assert(openref_secure_transport_open(&receiver, secured, opened, &result));
    assert(result == OPENREF_SECURITY_REPLAY_ACCEPT_FIRST);
    assert(memcmp(plain, opened, sizeof(plain)) == 0);
    assert(!openref_secure_transport_open(&receiver, secured, opened, &result));
    assert(result == OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE);
    assert(receiver.replay_rejections == 1u);

    openref_secure_transport_t final_counter;
    assert(openref_secure_transport_init(
        &final_counter, encrypt, decrypt, NULL, 7u, 2u, UINT32_MAX));
    assert(openref_secure_transport_protect(&final_counter, plain, secured));
    assert(final_counter.transmit_exhausted);
    assert(!openref_secure_transport_protect(&final_counter, plain, secured));
    assert(final_counter.protect_failures == 1u);
    assert(!openref_secure_transport_init(
        &sender, encrypt, decrypt, NULL, 0u, 2u, 1u));
    return 0;
}
