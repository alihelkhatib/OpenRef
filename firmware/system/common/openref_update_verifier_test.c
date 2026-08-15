#include <assert.h>
#include <string.h>

#include "openref_update_verifier.h"

typedef struct {
    bool signature_ok;
    uint8_t sum;
} crypto_state_t;

static bool verify_signature(void *context, const uint8_t *signed_data,
    const uint8_t *key_id, const uint8_t *signature)
{
    crypto_state_t *state = context;
    return state->signature_ok && signed_data[0] == 0x4fu &&
        key_id[0] == 0x33u && signature[0] == 0x5au;
}

static bool hash_begin(void *context)
{
    ((crypto_state_t *)context)->sum = 0u;
    return true;
}

static bool hash_update(void *context, const uint8_t *data, uint32_t length)
{
    crypto_state_t *state = context;
    for (uint32_t i = 0u; i < length; i++) {
        state->sum = (uint8_t)(state->sum + data[i]);
    }
    return true;
}

static bool hash_finish(void *context, uint8_t *digest)
{
    uint8_t sum = ((crypto_state_t *)context)->sum;
    for (uint8_t i = 0u; i < OPENREF_UPDATE_DIGEST_BYTES; i++) {
        digest[i] = (uint8_t)(sum + i);
    }
    return true;
}

static void write_u32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
    data[2] = (uint8_t)(value >> 16);
    data[3] = (uint8_t)(value >> 24);
}

static void make_manifest(uint8_t *wire, uint8_t target, uint32_t version,
                          uint32_t size, uint8_t image_sum)
{
    memset(wire, 0, OPENREF_UPDATE_MANIFEST_BYTES);
    wire[0] = 0x4fu;
    wire[1] = 0x52u;
    wire[2] = 0x55u;
    wire[3] = 0x50u;
    wire[4] = 1u;
    wire[5] = target;
    write_u32(&wire[8], 0x12345678u);
    write_u32(&wire[12], version);
    write_u32(&wire[16], 2u);
    write_u32(&wire[20], size);
    for (uint8_t i = 0u; i < OPENREF_UPDATE_DIGEST_BYTES; i++) {
        wire[24u + i] = (uint8_t)(image_sum + i);
    }
    memset(&wire[56], 0x22, 16u);
    memset(&wire[72], 0x33, OPENREF_UPDATE_KEY_ID_BYTES);
    wire[80] = 0x5au;
}

static openref_update_verifier_t make_verifier(crypto_state_t *state)
{
    openref_update_platform_t platform = {
        .target = OPENREF_UPDATE_TARGET_RADIO,
        .hardware_id = 0x12345678u,
        .bootloader_version = 3u,
        .antirollback_floor = 5u,
        .confirmed_image_version = 6u,
        .maximum_image_bytes = 1024u,
    };
    openref_update_crypto_t crypto = {
        verify_signature, hash_begin, hash_update, hash_finish, state,
    };
    openref_update_verifier_t verifier;
    assert(openref_update_verifier_init(&verifier, &platform, crypto));
    return verifier;
}

static void test_valid_streamed_image(void)
{
    crypto_state_t state = {.signature_ok = true};
    openref_update_verifier_t verifier = make_verifier(&state);
    uint8_t image[5] = {1u, 2u, 3u, 4u, 5u};
    uint8_t wire[OPENREF_UPDATE_MANIFEST_BYTES];
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, sizeof(image), 15u);
    assert(openref_update_verifier_begin(&verifier, wire));
    assert(openref_update_verifier_write(&verifier, image, 2u));
    assert(openref_update_verifier_write(&verifier, &image[2], 3u));
    assert(openref_update_verifier_finish(&verifier));
    assert(verifier.verified);
}

static void test_manifest_security_rejections(void)
{
    crypto_state_t state = {.signature_ok = true};
    uint8_t wire[OPENREF_UPDATE_MANIFEST_BYTES];
    openref_update_verifier_t verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_AUDIO, 7u, 5u, 15u);
    assert(!openref_update_verifier_begin(&verifier, wire));
    verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 6u, 5u, 15u);
    assert(!openref_update_verifier_begin(&verifier, wire));
    verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, 5u, 15u);
    state.signature_ok = false;
    assert(!openref_update_verifier_begin(&verifier, wire));

    state.signature_ok = true;
    verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, 5u, 15u);
    write_u32(&wire[8], 0x87654321u);
    assert(!openref_update_verifier_begin(&verifier, wire));
    verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, 5u, 15u);
    write_u32(&wire[16], 4u);
    assert(!openref_update_verifier_begin(&verifier, wire));
    verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, 1025u, 15u);
    assert(!openref_update_verifier_begin(&verifier, wire));
    verifier = make_verifier(&state);
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, 5u, 15u);
    wire[6] = 1u;
    assert(!openref_update_verifier_begin(&verifier, wire));
}

static void test_truncation_overflow_and_corruption(void)
{
    crypto_state_t state = {.signature_ok = true};
    uint8_t image[5] = {1u, 2u, 3u, 4u, 5u};
    uint8_t wire[OPENREF_UPDATE_MANIFEST_BYTES];
    make_manifest(wire, OPENREF_UPDATE_TARGET_RADIO, 7u, 5u, 15u);
    openref_update_verifier_t verifier = make_verifier(&state);
    assert(openref_update_verifier_begin(&verifier, wire));
    assert(openref_update_verifier_write(&verifier, image, 4u));
    assert(!openref_update_verifier_finish(&verifier));

    verifier = make_verifier(&state);
    assert(openref_update_verifier_begin(&verifier, wire));
    assert(!openref_update_verifier_write(&verifier, image, 6u));

    verifier = make_verifier(&state);
    assert(openref_update_verifier_begin(&verifier, wire));
    image[0] ^= 1u;
    assert(openref_update_verifier_write(&verifier, image, 5u));
    assert(!openref_update_verifier_finish(&verifier));
}

int main(void)
{
    test_valid_streamed_image();
    test_manifest_security_rejections();
    test_truncation_overflow_and_corruption();
    return 0;
}
