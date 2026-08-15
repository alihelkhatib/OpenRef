#include "openref_update_verifier.h"

#include <stddef.h>
#include <string.h>

static uint32_t read_u32(const uint8_t *data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8) |
        ((uint32_t)data[2] << 16) | ((uint32_t)data[3] << 24);
}

static bool nonzero(const uint8_t *data, uint8_t length)
{
    uint8_t value = 0u;
    for (uint8_t i = 0u; i < length; i++) {
        value |= data[i];
    }
    return value != 0u;
}

static bool equal_constant_time(const uint8_t *left, const uint8_t *right,
                                uint8_t length)
{
    uint8_t difference = 0u;
    for (uint8_t i = 0u; i < length; i++) {
        difference |= (uint8_t)(left[i] ^ right[i]);
    }
    return difference == 0u;
}

bool openref_update_verifier_init(openref_update_verifier_t *verifier,
    const openref_update_platform_t *platform, openref_update_crypto_t crypto)
{
    if (verifier == NULL || platform == NULL ||
        (platform->target != OPENREF_UPDATE_TARGET_RADIO &&
         platform->target != OPENREF_UPDATE_TARGET_AUDIO) ||
        platform->hardware_id == 0u || platform->bootloader_version == 0u ||
        platform->maximum_image_bytes == 0u || crypto.verify_signature == NULL ||
        crypto.hash_begin == NULL || crypto.hash_update == NULL ||
        crypto.hash_finish == NULL) {
        return false;
    }
    memset(verifier, 0, sizeof(*verifier));
    verifier->platform = *platform;
    verifier->crypto = crypto;
    return true;
}

bool openref_update_verifier_begin(openref_update_verifier_t *verifier,
    const uint8_t wire[OPENREF_UPDATE_MANIFEST_BYTES])
{
    if (verifier == NULL || wire == NULL || verifier->active ||
        wire[0] != 0x4fu || wire[1] != 0x52u || wire[2] != 0x55u ||
        wire[3] != 0x50u || wire[4] != 1u || wire[6] != 0u || wire[7] != 0u) {
        if (verifier != NULL) {
            verifier->rejected_manifests++;
        }
        return false;
    }
    openref_update_manifest_t manifest = {
        .target = wire[5],
        .hardware_id = read_u32(&wire[8]),
        .image_version = read_u32(&wire[12]),
        .minimum_bootloader_version = read_u32(&wire[16]),
        .image_size = read_u32(&wire[20]),
    };
    memcpy(manifest.digest, &wire[24], sizeof(manifest.digest));
    memcpy(manifest.release_id, &wire[56], sizeof(manifest.release_id));
    memcpy(manifest.key_id, &wire[72], sizeof(manifest.key_id));
    bool valid = manifest.target == verifier->platform.target &&
        manifest.hardware_id == verifier->platform.hardware_id &&
        manifest.image_version >= verifier->platform.antirollback_floor &&
        manifest.image_version > verifier->platform.confirmed_image_version &&
        manifest.minimum_bootloader_version <= verifier->platform.bootloader_version &&
        manifest.image_size > 0u &&
        manifest.image_size <= verifier->platform.maximum_image_bytes &&
        nonzero(manifest.digest, sizeof(manifest.digest)) &&
        nonzero(manifest.release_id, sizeof(manifest.release_id)) &&
        nonzero(manifest.key_id, sizeof(manifest.key_id)) &&
        verifier->crypto.verify_signature(verifier->crypto.context, wire,
            manifest.key_id, &wire[OPENREF_UPDATE_SIGNED_BYTES]);
    if (!valid || !verifier->crypto.hash_begin(verifier->crypto.context)) {
        verifier->rejected_manifests++;
        return false;
    }
    verifier->manifest = manifest;
    verifier->received_bytes = 0u;
    verifier->verified = false;
    verifier->active = true;
    return true;
}

bool openref_update_verifier_write(openref_update_verifier_t *verifier,
    const uint8_t *image_data, uint32_t length)
{
    if (verifier == NULL || !verifier->active || image_data == NULL ||
        length == 0u || verifier->received_bytes > verifier->manifest.image_size ||
        length > verifier->manifest.image_size -
            verifier->received_bytes ||
        !verifier->crypto.hash_update(verifier->crypto.context, image_data,
                                      length)) {
        if (verifier != NULL) {
            verifier->active = false;
            verifier->hash_failures++;
        }
        return false;
    }
    verifier->received_bytes += length;
    return true;
}

bool openref_update_verifier_finish(openref_update_verifier_t *verifier)
{
    if (verifier == NULL || !verifier->active ||
        verifier->received_bytes != verifier->manifest.image_size) {
        if (verifier != NULL) {
            verifier->active = false;
            verifier->hash_failures++;
        }
        return false;
    }
    uint8_t digest[OPENREF_UPDATE_DIGEST_BYTES];
    bool valid = verifier->crypto.hash_finish(verifier->crypto.context, digest) &&
        equal_constant_time(digest, verifier->manifest.digest, sizeof(digest));
    verifier->active = false;
    verifier->verified = valid;
    if (!valid) {
        verifier->hash_failures++;
    }
    return valid;
}
