#include "openref_security_fg23.h"

#include <stddef.h>

#ifdef OPENREF_APP_SECURITY

bool openref_security_fg23_init(
    openref_security_fg23_t *security,
    const uint8_t crew_session_key[16])
{
    if (security == NULL || crew_session_key == NULL) {
        return false;
    }
    *security = (openref_security_fg23_t){0};
    for (uint8_t index = 0u; index < sizeof(security->key_material); index++) {
        security->key_material[index] = crew_session_key[index];
    }
    sl_se_command_context_t command_context = SL_SE_COMMAND_CONTEXT_INIT;
    security->command_context = command_context;
    security->key_descriptor.type = SL_SE_KEY_TYPE_AES_128;
    security->key_descriptor.flags = 0u;
    security->key_descriptor.storage.method = SL_SE_KEY_STORAGE_EXTERNAL_PLAINTEXT;
    security->key_descriptor.storage.location.buffer.pointer = security->key_material;
    security->key_descriptor.storage.location.buffer.size = sizeof(security->key_material);
    if (sl_se_init() != SL_STATUS_OK ||
        sl_se_validate_key(&security->key_descriptor) != SL_STATUS_OK) {
        return false;
    }
    security->initialized = true;
    return true;
}

bool openref_security_fg23_encrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t tag[OPENREF_SECURITY_TAG_BYTES])
{
    openref_security_fg23_t *security = context;
    if (security == NULL || !security->initialized || nonce == NULL ||
        aad == NULL || plaintext == NULL || ciphertext == NULL || tag == NULL) {
        return false;
    }
    return sl_se_ccm_encrypt_and_tag(
        &security->command_context, &security->key_descriptor,
        OPENREF_SECURITY_PLAINTEXT_BYTES, nonce, OPENREF_SECURITY_NONCE_BYTES,
        aad, OPENREF_SECURITY_AAD_BYTES, plaintext, ciphertext, tag,
        OPENREF_SECURITY_TAG_BYTES) == SL_STATUS_OK;
}

bool openref_security_fg23_decrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    const uint8_t tag[OPENREF_SECURITY_TAG_BYTES],
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES])
{
    openref_security_fg23_t *security = context;
    if (security == NULL || !security->initialized || nonce == NULL ||
        aad == NULL || ciphertext == NULL || tag == NULL || plaintext == NULL) {
        return false;
    }
    return sl_se_ccm_auth_decrypt(
        &security->command_context, &security->key_descriptor,
        OPENREF_SECURITY_PLAINTEXT_BYTES, nonce, OPENREF_SECURITY_NONCE_BYTES,
        aad, OPENREF_SECURITY_AAD_BYTES, ciphertext, plaintext, tag,
        OPENREF_SECURITY_TAG_BYTES) == SL_STATUS_OK;
}

#else

bool openref_security_fg23_init(
    openref_security_fg23_t *security,
    const uint8_t crew_session_key[16])
{
    (void)security;
    (void)crew_session_key;
    return false;
}

bool openref_security_fg23_encrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t tag[OPENREF_SECURITY_TAG_BYTES])
{
    (void)context; (void)nonce; (void)aad; (void)plaintext;
    (void)ciphertext; (void)tag;
    return false;
}

bool openref_security_fg23_decrypt(
    void *context,
    const uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES],
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t ciphertext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    const uint8_t tag[OPENREF_SECURITY_TAG_BYTES],
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES])
{
    (void)context; (void)nonce; (void)aad; (void)ciphertext;
    (void)tag; (void)plaintext;
    return false;
}

#endif
