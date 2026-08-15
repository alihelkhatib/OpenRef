#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "openref_security.h"

static uint8_t make_tag(
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES])
{
    uint8_t tag = 0u;
    for (uint8_t index = 0u; index < OPENREF_SECURITY_NONCE_BYTES; index++) {
        tag ^= nonce[index];
    }
    for (uint8_t index = 0u; index < OPENREF_SECURITY_AAD_BYTES; index++) {
        tag ^= aad[index];
    }
    for (uint8_t index = 0u; index < OPENREF_SECURITY_PLAINTEXT_BYTES; index++) {
        tag ^= ciphertext[index];
    }
    return tag;
}

static bool fake_encrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t tag[OPENREF_SECURITY_TAG_BYTES])
{
    (void)context;
    for (uint8_t index = 0u; index < OPENREF_SECURITY_PLAINTEXT_BYTES; index++) {
        ciphertext[index] = plaintext[index] ^ nonce[index % OPENREF_SECURITY_NONCE_BYTES];
    }
    memset(tag, make_tag(nonce, aad, ciphertext), OPENREF_SECURITY_TAG_BYTES);
    return true;
}

static bool fake_decrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    const uint8_t tag[OPENREF_SECURITY_TAG_BYTES],
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES])
{
    (void)context;
    uint8_t expected = make_tag(nonce, aad, ciphertext);
    for (uint8_t index = 0u; index < OPENREF_SECURITY_TAG_BYTES; index++) {
        if (tag[index] != expected) {
            return false;
        }
    }
    for (uint8_t index = 0u; index < OPENREF_SECURITY_PLAINTEXT_BYTES; index++) {
        plaintext[index] = ciphertext[index] ^ nonce[index % OPENREF_SECURITY_NONCE_BYTES];
    }
    return true;
}

int main(void)
{
    uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES];
    openref_security_build_nonce(0x01020304u, 5u, 0x11121314u,
                                 0x21222324u, nonce);
    const uint8_t expected[OPENREF_SECURITY_NONCE_BYTES] = {
        0x04u, 0x03u, 0x02u, 0x01u, 0x05u,
        0x14u, 0x13u, 0x12u, 0x11u,
        0x24u, 0x23u, 0x22u, 0x21u,
    };
    for (uint8_t index = 0u; index < OPENREF_SECURITY_NONCE_BYTES; index++) {
        assert(nonce[index] == expected[index]);
    }

    openref_security_replay_state_t state = {0};
    assert(openref_security_accept_authenticated(&state, 7u, 100u) ==
           OPENREF_SECURITY_REPLAY_ACCEPT_FIRST);
    assert(openref_security_accept_authenticated(&state, 7u, 102u) ==
           OPENREF_SECURITY_REPLAY_ACCEPT_NEW);
    assert(openref_security_accept_authenticated(&state, 7u, 101u) ==
           OPENREF_SECURITY_REPLAY_ACCEPT_REORDERED);
    assert(openref_security_accept_authenticated(&state, 7u, 101u) ==
           OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE);
    assert(openref_security_accept_authenticated(&state, 7u, 30u) ==
           OPENREF_SECURITY_REPLAY_REJECT_STALE);
    assert(openref_security_accept_authenticated(&state, 6u, 1000u) ==
           OPENREF_SECURITY_REPLAY_REJECT_OLD_BOOT);
    assert(openref_security_accept_authenticated(&state, 8u, 0u) ==
           OPENREF_SECURITY_REPLAY_ACCEPT_NEW);

    uint8_t aad[OPENREF_SECURITY_AAD_BYTES] = {0};
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES];
    for (uint8_t index = 0u; index < OPENREF_SECURITY_PLAINTEXT_BYTES; index++) {
        plaintext[index] = index;
    }
    uint8_t envelope[OPENREF_SECURITY_ENVELOPE_BYTES];
    assert(openref_security_protect(
        fake_encrypt, NULL, 9u, 2u, 4u, 10u, aad, plaintext, envelope));
    uint8_t opened[OPENREF_SECURITY_PLAINTEXT_BYTES];
    openref_security_replay_state_t protected_replay = {0};
    openref_security_replay_result_t replay_result;
    assert(openref_security_open(
        fake_decrypt, NULL, 9u, 2u, aad, envelope, &protected_replay,
        opened, &replay_result));
    assert(replay_result == OPENREF_SECURITY_REPLAY_ACCEPT_FIRST);
    assert(memcmp(opened, plaintext, sizeof(opened)) == 0);
    assert(!openref_security_open(
        fake_decrypt, NULL, 9u, 2u, aad, envelope, &protected_replay,
        opened, &replay_result));
    assert(replay_result == OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE);

    assert(openref_security_protect(
        fake_encrypt, NULL, 9u, 2u, 4u, 11u, aad, plaintext, envelope));
    envelope[OPENREF_SECURITY_ENVELOPE_BYTES - 1u] ^= 1u;
    assert(!openref_security_open(
        fake_decrypt, NULL, 9u, 2u, aad, envelope, &protected_replay,
        opened, &replay_result));
    envelope[OPENREF_SECURITY_ENVELOPE_BYTES - 1u] ^= 1u;
    assert(openref_security_open(
        fake_decrypt, NULL, 9u, 2u, aad, envelope, &protected_replay,
        opened, &replay_result));
    assert(replay_result == OPENREF_SECURITY_REPLAY_ACCEPT_NEW);
    return 0;
}
