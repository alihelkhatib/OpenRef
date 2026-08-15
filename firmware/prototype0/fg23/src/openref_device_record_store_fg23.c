#include "openref_device_record_store_fg23.h"

#include <stddef.h>

#ifdef OPENREF_APP_DEVICE_RECORD_NVM3

#include "nvm3_default.h"

#define OPENREF_DEVICE_RECORD_SLOT_A_NVM3_KEY ((nvm3_ObjectKey_t)0x0f5230u)
#define OPENREF_DEVICE_RECORD_SLOT_B_NVM3_KEY ((nvm3_ObjectKey_t)0x0f5231u)

static bool slot_key(uint8_t slot, nvm3_ObjectKey_t *key)
{
    if (key == NULL || slot > 1u) return false;
    *key = slot == 0u ? OPENREF_DEVICE_RECORD_SLOT_A_NVM3_KEY
                      : OPENREF_DEVICE_RECORD_SLOT_B_NVM3_KEY;
    return true;
}

static bool read_slot(void *context, uint8_t slot,
                      uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    nvm3_ObjectKey_t key = 0u;
    uint32_t object_type = 0u;
    size_t object_length = 0u;
    (void)context;
    if (record == NULL || !slot_key(slot, &key) ||
        nvm3_initDefault() != SL_STATUS_OK ||
        nvm3_getObjectInfo(nvm3_defaultHandle, key, &object_type,
                           &object_length) != SL_STATUS_OK ||
        object_type != NVM3_OBJECTTYPE_DATA ||
        object_length != OPENREF_CONFIG_SLOT_BYTES) {
        return false;
    }
    return nvm3_readData(nvm3_defaultHandle, key, record,
                         OPENREF_CONFIG_SLOT_BYTES) == SL_STATUS_OK;
}

static bool write_slot(void *context, uint8_t slot,
                       const uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    nvm3_ObjectKey_t key = 0u;
    (void)context;
    return record != NULL && slot_key(slot, &key) &&
        nvm3_initDefault() == SL_STATUS_OK &&
        nvm3_writeData(nvm3_defaultHandle, key, record,
                       OPENREF_CONFIG_SLOT_BYTES) == SL_STATUS_OK;
}

#else

static bool read_slot(void *context, uint8_t slot,
                      uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    (void)context; (void)slot; (void)record;
    return false;
}

static bool write_slot(void *context, uint8_t slot,
                       const uint8_t record[OPENREF_CONFIG_SLOT_BYTES])
{
    (void)context; (void)slot; (void)record;
    return false;
}

#endif

openref_config_backend_t openref_device_record_store_fg23_backend(void)
{
    openref_config_backend_t backend = {read_slot, write_slot, NULL};
    return backend;
}
