#ifndef OPENREF_SECURITY_FG23_H
#define OPENREF_SECURITY_FG23_H

#include <stdbool.h>
#include <stdint.h>

#include "openref_security.h"

#ifdef OPENREF_APP_SECURITY
#include "sl_se_manager.h"
#include "sl_se_manager_cipher.h"
#include "sl_se_manager_types.h"
#endif

#ifdef OPENREF_APP_SECURITY
typedef struct {
    sl_se_command_context_t command_context;
    sl_se_key_descriptor_t key_descriptor;
    uint8_t key_material[16];
    bool initialized;
} openref_security_fg23_t;
#else
typedef struct {
    bool initialized;
} openref_security_fg23_t;
#endif

bool openref_security_fg23_init(
    openref_security_fg23_t *security,
    const uint8_t crew_session_key[16]);

bool openref_security_fg23_encrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t tag[OPENREF_SECURITY_TAG_BYTES]);

bool openref_security_fg23_decrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    const uint8_t tag[OPENREF_SECURITY_TAG_BYTES],
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES]);

#endif
