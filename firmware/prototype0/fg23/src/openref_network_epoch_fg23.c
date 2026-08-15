#include "openref_network_epoch_fg23.h"

#include <stddef.h>

#ifdef OPENREF_APP_NETWORK_EPOCH_NVM3

#include "nvm3_default.h"

#define OPENREF_NETWORK_EPOCH_NVM3_KEY ((nvm3_ObjectKey_t)0x0f5202u)

static bool read_epoch(uint32_t *value, bool *found)
{
    uint32_t object_type = 0u;
    size_t object_length = 0u;
    sl_status_t status = nvm3_getObjectInfo(
        nvm3_defaultHandle, OPENREF_NETWORK_EPOCH_NVM3_KEY,
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
    status = nvm3_readData(nvm3_defaultHandle,
        OPENREF_NETWORK_EPOCH_NVM3_KEY, value, sizeof(*value));
    *found = status == SL_STATUS_OK;
    return *found;
}

bool openref_network_epoch_fg23_load(uint32_t *persisted_epoch)
{
    if (persisted_epoch == NULL || nvm3_initDefault() != SL_STATUS_OK) {
        return false;
    }
    bool found = false;
    if (!read_epoch(persisted_epoch, &found)) {
        return false;
    }
    if (!found) {
        *persisted_epoch = 0u;
    }
    return true;
}

bool openref_network_epoch_fg23_advance(void *context, uint32_t current_epoch,
    uint32_t *persisted_next_epoch)
{
    (void)context;
    if (persisted_next_epoch == NULL || current_epoch == UINT32_MAX ||
        nvm3_initDefault() != SL_STATUS_OK) {
        return false;
    }
    uint32_t stored = 0u;
    bool found = false;
    if (!read_epoch(&stored, &found) ||
        (found && stored != current_epoch) || (!found && current_epoch != 0u)) {
        return false;
    }
    uint32_t next = current_epoch + 1u;
    if (nvm3_writeData(nvm3_defaultHandle, OPENREF_NETWORK_EPOCH_NVM3_KEY,
                       &next, sizeof(next)) != SL_STATUS_OK) {
        return false;
    }
    uint32_t verified = 0u;
    bool verify_found = false;
    if (!read_epoch(&verified, &verify_found) || !verify_found ||
        verified != next) {
        return false;
    }
    *persisted_next_epoch = next;
    return true;
}

#else

bool openref_network_epoch_fg23_load(uint32_t *persisted_epoch)
{
    (void)persisted_epoch;
    return false;
}

bool openref_network_epoch_fg23_advance(void *context, uint32_t current_epoch,
    uint32_t *persisted_next_epoch)
{
    (void)context;
    (void)current_epoch;
    (void)persisted_next_epoch;
    return false;
}

#endif
