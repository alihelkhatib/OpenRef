#ifndef OPENREF_RT595_SLOT_AUTHENTICATOR_H
#define OPENREF_RT595_SLOT_AUTHENTICATOR_H
#include <stdbool.h>
#include <stdint.h>
#include "openref_boot_policy.h"
#include "openref_update_verifier.h"
#define OPENREF_RT595_SLOT_AUTH_CHUNK_BYTES 256u
typedef bool (*openref_rt595_slot_read_fn)(void *,uint32_t,uint8_t *,uint32_t);
typedef struct {openref_rt595_slot_read_fn read;void *context;} openref_rt595_slot_reader_t;
typedef struct {openref_rt595_slot_reader_t reader;openref_update_platform_t platform;openref_update_crypto_t crypto;uint32_t manifest_base[2],image_base[2],image_capacity[2],authenticated_image_size[2],failures,read_failures;bool initialized;} openref_rt595_slot_authenticator_t;
bool openref_rt595_slot_authenticator_init(openref_rt595_slot_authenticator_t *,openref_rt595_slot_reader_t,const openref_update_platform_t *,openref_update_crypto_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);
/* running_slot may be OPENREF_BOOT_NO_SLOT while executing from the immutable
 * bootstrap.  An application must identify its own slot so it cannot request
 * authentication of the flash region from which it is executing. */
bool openref_rt595_slot_authenticate(openref_rt595_slot_authenticator_t *,uint8_t candidate_slot,uint8_t running_slot,openref_boot_slot_t *);
#endif
