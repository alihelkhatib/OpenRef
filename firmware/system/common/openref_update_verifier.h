#ifndef OPENREF_UPDATE_VERIFIER_H
#define OPENREF_UPDATE_VERIFIER_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_UPDATE_MANIFEST_BYTES 144u
#define OPENREF_UPDATE_SIGNED_BYTES 80u
#define OPENREF_UPDATE_DIGEST_BYTES 32u
#define OPENREF_UPDATE_SIGNATURE_BYTES 64u
#define OPENREF_UPDATE_KEY_ID_BYTES 8u

#define OPENREF_UPDATE_TARGET_RADIO 1u
#define OPENREF_UPDATE_TARGET_AUDIO 2u

typedef bool (*openref_update_signature_verify_fn)(
    void *context,
    const uint8_t signed_data[OPENREF_UPDATE_SIGNED_BYTES],
    const uint8_t key_id[OPENREF_UPDATE_KEY_ID_BYTES],
    const uint8_t signature[OPENREF_UPDATE_SIGNATURE_BYTES]);
typedef bool (*openref_update_hash_begin_fn)(void *context);
typedef bool (*openref_update_hash_update_fn)(
    void *context, const uint8_t *data, uint32_t length);
typedef bool (*openref_update_hash_finish_fn)(
    void *context, uint8_t digest[OPENREF_UPDATE_DIGEST_BYTES]);

typedef struct {
    openref_update_signature_verify_fn verify_signature;
    openref_update_hash_begin_fn hash_begin;
    openref_update_hash_update_fn hash_update;
    openref_update_hash_finish_fn hash_finish;
    void *context;
} openref_update_crypto_t;

typedef struct {
    uint8_t target;
    uint32_t hardware_id;
    uint32_t bootloader_version;
    uint32_t antirollback_floor;
    uint32_t confirmed_image_version;
    uint32_t maximum_image_bytes;
} openref_update_platform_t;

typedef struct {
    uint8_t target;
    uint32_t hardware_id;
    uint32_t image_version;
    uint32_t minimum_bootloader_version;
    uint32_t image_size;
    uint8_t digest[OPENREF_UPDATE_DIGEST_BYTES];
    uint8_t release_id[16];
    uint8_t key_id[OPENREF_UPDATE_KEY_ID_BYTES];
} openref_update_manifest_t;

typedef struct {
    openref_update_platform_t platform;
    openref_update_crypto_t crypto;
    openref_update_manifest_t manifest;
    uint32_t received_bytes;
    uint32_t rejected_manifests;
    uint32_t hash_failures;
    bool active;
    bool verified;
} openref_update_verifier_t;

bool openref_update_verifier_init(
    openref_update_verifier_t *verifier,
    const openref_update_platform_t *platform,
    openref_update_crypto_t crypto);

bool openref_update_verifier_begin(
    openref_update_verifier_t *verifier,
    const uint8_t manifest_wire[OPENREF_UPDATE_MANIFEST_BYTES]);

bool openref_update_verifier_write(
    openref_update_verifier_t *verifier,
    const uint8_t *image_data,
    uint32_t length);

bool openref_update_verifier_finish(openref_update_verifier_t *verifier);

#endif
