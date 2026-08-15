#include "openref_boot_counter_fg23.h"

#include <stddef.h>

#include "openref_boot_counter.h"

#ifdef OPENREF_APP_SECURITY_NVM3

#include "nvm3_default.h"

#define OPENREF_BOOT_COUNTER_NVM3_KEY ((nvm3_ObjectKey_t)0x0f5201u)

static bool read_counter(void *context, uint32_t *value, bool *found)
{
    (void)context;
    uint32_t object_type = 0u;
    size_t object_length = 0u;
    sl_status_t status = nvm3_getObjectInfo(
        nvm3_defaultHandle, OPENREF_BOOT_COUNTER_NVM3_KEY,
        &object_type, &object_length);
    if (status == ECODE_NVM3_ERR_KEY_NOT_FOUND) {
        *value = 0u;
        *found = false;
        return true;
    }
    if (status != SL_STATUS_OK || object_type != NVM3_OBJECTTYPE_DATA ||
        object_length != sizeof(*value)) {
        return false;
    }
    status = nvm3_readData(
        nvm3_defaultHandle, OPENREF_BOOT_COUNTER_NVM3_KEY,
        value, sizeof(*value));
    *found = status == SL_STATUS_OK;
    return *found;
}

static bool write_counter(void *context, uint32_t value)
{
    (void)context;
    return nvm3_writeData(
        nvm3_defaultHandle, OPENREF_BOOT_COUNTER_NVM3_KEY,
        &value, sizeof(value)) == SL_STATUS_OK;
}

bool openref_boot_counter_fg23_advance(uint32_t *active_boot_counter)
{
    if (active_boot_counter == NULL || nvm3_initDefault() != SL_STATUS_OK) {
        return false;
    }
    return openref_boot_counter_advance(
        read_counter, write_counter, NULL, active_boot_counter);
}

#else

bool openref_boot_counter_fg23_advance(uint32_t *active_boot_counter)
{
    (void)active_boot_counter;
    return false;
}

#endif
