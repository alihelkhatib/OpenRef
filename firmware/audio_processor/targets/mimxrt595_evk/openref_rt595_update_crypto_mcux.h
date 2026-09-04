#ifndef OPENREF_RT595_UPDATE_CRYPTO_MCUX_H
#define OPENREF_RT595_UPDATE_CRYPTO_MCUX_H
#include "fsl_hashcrypt.h"
#include "openref_rt595_update_crypto.h"
typedef struct {openref_rt595_update_crypto_t crypto;hashcrypt_hash_ctx_t hash;} openref_rt595_update_crypto_mcux_t;
bool openref_rt595_update_crypto_mcux_init(openref_rt595_update_crypto_mcux_t *,const uint8_t[8],const uint8_t[64]);
#endif
