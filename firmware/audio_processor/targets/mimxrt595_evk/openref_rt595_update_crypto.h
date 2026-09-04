#ifndef OPENREF_RT595_UPDATE_CRYPTO_H
#define OPENREF_RT595_UPDATE_CRYPTO_H
#include <stdbool.h>
#include <stdint.h>
#include "openref_update_verifier.h"
#define OPENREF_RT595_P256_PUBLIC_KEY_BYTES 64u
#ifdef OPENREF_HAS_TRUST_ANCHOR
#include "openref_trust_anchor_generated.h"
#endif
typedef bool (*openref_rt595_sha_begin_fn)(void *);
typedef bool (*openref_rt595_sha_update_fn)(void *,const uint8_t *,uint32_t);
typedef bool (*openref_rt595_sha_finish_fn)(void *,uint8_t[32]);
typedef bool (*openref_rt595_p256_verify_fn)(void *,const uint8_t[64],const uint8_t[32],const uint8_t[64]);
typedef struct {openref_rt595_sha_begin_fn begin;openref_rt595_sha_update_fn update;openref_rt595_sha_finish_fn finish;openref_rt595_p256_verify_fn verify;void *context;} openref_rt595_update_crypto_driver_t;
typedef struct {openref_rt595_update_crypto_driver_t driver;uint8_t key_id[8];uint8_t public_key[64];uint32_t rejected_keys,failures;bool initialized;} openref_rt595_update_crypto_t;
bool openref_rt595_update_crypto_init(openref_rt595_update_crypto_t *,openref_rt595_update_crypto_driver_t,const uint8_t[8],const uint8_t[64]);
openref_update_crypto_t openref_rt595_update_crypto_callbacks(openref_rt595_update_crypto_t *);
#endif
