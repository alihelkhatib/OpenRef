#ifndef OPENREF_SECURITY_H
#define OPENREF_SECURITY_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_SECURITY_NONCE_BYTES 13u
#define OPENREF_SECURITY_PREFIX_BYTES 8u
#define OPENREF_SECURITY_TAG_BYTES 8u
#define OPENREF_SECURITY_OVERHEAD_BYTES 16u
#define OPENREF_SECURITY_REPLAY_WINDOW_BITS 64u
#define OPENREF_SECURITY_AAD_BYTES 18u
#define OPENREF_SECURITY_PLAINTEXT_BYTES 80u
#define OPENREF_SECURITY_ENVELOPE_BYTES 96u

typedef bool (*openref_security_ccm_encrypt_fn)(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t tag[OPENREF_SECURITY_TAG_BYTES]);

typedef bool (*openref_security_ccm_decrypt_fn)(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    const uint8_t tag[OPENREF_SECURITY_TAG_BYTES],
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES]);

typedef enum {
    OPENREF_SECURITY_REPLAY_ACCEPT_FIRST = 0,
    OPENREF_SECURITY_REPLAY_ACCEPT_NEW = 1,
    OPENREF_SECURITY_REPLAY_ACCEPT_REORDERED = 2,
    OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE = 3,
    OPENREF_SECURITY_REPLAY_REJECT_STALE = 4,
    OPENREF_SECURITY_REPLAY_REJECT_OLD_BOOT = 5
} openref_security_replay_result_t;

typedef struct {
    uint32_t boot_counter;
    uint32_t highest_packet_counter;
    uint64_t received_bitmap;
    bool initialized;
} openref_security_replay_state_t;

void openref_security_build_nonce(
    uint32_t crew_session_id,
    uint8_t source_id,
    uint32_t boot_counter,
    uint32_t packet_counter,
    uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES]);

openref_security_replay_result_t openref_security_accept_authenticated(
    openref_security_replay_state_t *state,
    uint32_t boot_counter,
    uint32_t packet_counter);

bool openref_security_protect(
    openref_security_ccm_encrypt_fn encrypt,
    void *context,
    uint32_t crew_session_id,
    uint8_t source_id,
    uint32_t boot_counter,
    uint32_t packet_counter,
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t envelope[OPENREF_SECURITY_ENVELOPE_BYTES]);

bool openref_security_open(
    openref_security_ccm_decrypt_fn decrypt,
    void *context,
    uint32_t crew_session_id,
    uint8_t source_id,
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t envelope[OPENREF_SECURITY_ENVELOPE_BYTES],
    openref_security_replay_state_t *replay,
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    openref_security_replay_result_t *replay_result);

#ifdef __cplusplus
}
#endif

#endif
