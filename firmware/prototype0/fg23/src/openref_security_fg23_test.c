#include <assert.h>
#include <stdint.h>

#include "openref_security_fg23.h"

int main(void)
{
    openref_security_fg23_t security = {0};
    uint8_t key[16] = {0};
    uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES] = {0};
    uint8_t aad[OPENREF_SECURITY_AAD_BYTES] = {0};
    uint8_t input[OPENREF_SECURITY_PLAINTEXT_BYTES] = {0};
    uint8_t output[OPENREF_SECURITY_PLAINTEXT_BYTES] = {0};
    uint8_t tag[OPENREF_SECURITY_TAG_BYTES] = {0};
    assert(!openref_security_fg23_init(&security, key));
    assert(!openref_security_fg23_encrypt(
        &security, nonce, aad, input, output, tag));
    assert(!openref_security_fg23_decrypt(
        &security, nonce, aad, input, tag, output));
    return 0;
}
