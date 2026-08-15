#include "openref_security_counters_fg23.h"

#include <stddef.h>

#ifdef OPENREF_APP_SECURITY_COUNTERS_NVM3

#include "nvm3_default.h"

#define OPENREF_ADMISSION_COUNTER_NVM3_KEY ((nvm3_ObjectKey_t)0x0f5203u)
#define OPENREF_SERVICE_COUNTER_NVM3_KEY ((nvm3_ObjectKey_t)0x0f5204u)

static bool domain_key(openref_security_counter_domain_t domain,
                       nvm3_ObjectKey_t *key)
{
    if (key == NULL) {
        return false;
    }
    if (domain == OPENREF_COUNTER_ADMISSION) {
        *key = OPENREF_ADMISSION_COUNTER_NVM3_KEY;
        return true;
    }
    if (domain == OPENREF_COUNTER_SERVICE) {
        *key = OPENREF_SERVICE_COUNTER_NVM3_KEY;
        return true;
    }
    return false;
}

static bool read_counter(nvm3_ObjectKey_t key, uint32_t *value, bool *found)
{
    uint32_t object_type = 0u;
    size_t object_length = 0u;
    sl_status_t status = nvm3_getObjectInfo(
        nvm3_defaultHandle, key, &object_type, &object_length);
    if (status == ECODE_NVM3_ERR_KEY_NOT_FOUND) {
        *value = 0u;
        *found = false;
        return true;
    }
    if (status != SL_STATUS_OK || object_type != NVM3_OBJECTTYPE_DATA ||
        object_length != sizeof(*value)) {
        return false;
    }
    status = nvm3_readData(nvm3_defaultHandle, key, value, sizeof(*value));
    *found = status == SL_STATUS_OK;
    return *found;
}

bool openref_security_counter_fg23_load(
    openref_security_counter_domain_t domain, uint32_t *persisted_counter)
{
    nvm3_ObjectKey_t key = 0u;
    if (persisted_counter == NULL || !domain_key(domain, &key) ||
        nvm3_initDefault() != SL_STATUS_OK) {
        return false;
    }
    bool found = false;
    if (!read_counter(key, persisted_counter, &found)) {
        return false;
    }
    if (!found) {
        *persisted_counter = 0u;
    }
    return true;
}

bool openref_security_counter_fg23_persist(void *context, uint32_t next_counter)
{
    openref_security_counter_context_t *counter_context = context;
    nvm3_ObjectKey_t key = 0u;
    if (counter_context == NULL || next_counter == 0u ||
        !domain_key(counter_context->domain, &key) ||
        nvm3_initDefault() != SL_STATUS_OK) {
        return false;
    }
    uint32_t stored = 0u;
    bool found = false;
    if (!read_counter(key, &stored, &found) ||
        (found && next_counter <= stored)) {
        return false;
    }
    if (nvm3_writeData(nvm3_defaultHandle, key, &next_counter,
                       sizeof(next_counter)) != SL_STATUS_OK) {
        return false;
    }
    uint32_t verified = 0u;
    bool verify_found = false;
    return read_counter(key, &verified, &verify_found) && verify_found &&
        verified == next_counter;
}

#else

bool openref_security_counter_fg23_load(
    openref_security_counter_domain_t domain, uint32_t *persisted_counter)
{
    (void)domain;
    (void)persisted_counter;
    return false;
}

bool openref_security_counter_fg23_persist(void *context, uint32_t next_counter)
{
    (void)context;
    (void)next_counter;
    return false;
}

#endif
