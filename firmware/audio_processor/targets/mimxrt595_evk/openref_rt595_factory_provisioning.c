#include "openref_rt595_factory_provisioning.h"

#include <stddef.h>

static bool valid(const openref_rt595_factory_driver_t *driver,
                  const openref_rt595_factory_plan_t *plan)
{
    uint8_t index;

    if (driver == NULL || plan == NULL ||
        driver->manufacturing_authorized == NULL ||
        driver->lock_is_set == NULL || driver->probe == NULL ||
        driver->program_blank == NULL || driver->readback_equal == NULL ||
        driver->set_lock_once == NULL) {
        return false;
    }
    for (index = 0u; index < OPENREF_RT595_FACTORY_REGION_COUNT; index++) {
        if (plan->region[index].bytes == NULL ||
            plan->region[index].length == 0u) {
            return false;
        }
    }
    return true;
}

openref_rt595_factory_result_t openref_rt595_factory_provision(
    const openref_rt595_factory_driver_t *driver,
    const openref_rt595_factory_plan_t *plan)
{
    bool locked = false;
    uint8_t index;
    openref_rt595_factory_probe_t state[OPENREF_RT595_FACTORY_REGION_COUNT];

    if (!valid(driver, plan)) {
        return OPENREF_RT595_FACTORY_FAILED;
    }
    /* Authorization must be a physical jig/strap seam, never normal
     * application UI. */
    if (!driver->manufacturing_authorized(driver->context)) {
        return OPENREF_RT595_FACTORY_UNAUTHORIZED;
    }
    if (!driver->lock_is_set(driver->context, &locked)) {
        return OPENREF_RT595_FACTORY_FAILED;
    }
    for (index = 0u; index < OPENREF_RT595_FACTORY_REGION_COUNT; index++) {
        state[index] = driver->probe(
            driver->context, (openref_rt595_factory_region_t)index,
            plan->region[index].bytes, plan->region[index].length);
        if (state[index] == OPENREF_RT595_FACTORY_PROBE_IO) {
            return OPENREF_RT595_FACTORY_FAILED;
        }
        if (state[index] == OPENREF_RT595_FACTORY_PROBE_OTHER_VALID ||
            state[index] == OPENREF_RT595_FACTORY_PROBE_CORRUPT) {
            return locked ? OPENREF_RT595_FACTORY_LOCKED_MISMATCH
                          : OPENREF_RT595_FACTORY_NONBLANK;
        }
    }
    if (locked) {
        for (index = 0u; index < OPENREF_RT595_FACTORY_REGION_COUNT; index++) {
            if (state[index] != OPENREF_RT595_FACTORY_PROBE_MATCH) {
                return OPENREF_RT595_FACTORY_LOCKED_MISMATCH;
            }
        }
        return OPENREF_RT595_FACTORY_ALREADY_PROVISIONED;
    }

    /* Identity/trust metadata is last and acts as the provisioning commit
     * record. */
    for (index = 0u; index < OPENREF_RT595_FACTORY_REGION_COUNT; index++) {
        if (state[index] == OPENREF_RT595_FACTORY_PROBE_BLANK &&
            !driver->program_blank(
                driver->context, (openref_rt595_factory_region_t)index,
                plan->region[index].bytes, plan->region[index].length)) {
            return OPENREF_RT595_FACTORY_WRITE_FAILED;
        }
        if (!driver->readback_equal(
                driver->context, (openref_rt595_factory_region_t)index,
                plan->region[index].bytes, plan->region[index].length)) {
            return OPENREF_RT595_FACTORY_VERIFY_FAILED;
        }
    }
    if (!driver->set_lock_once(driver->context) ||
        !driver->lock_is_set(driver->context, &locked) || !locked) {
        return OPENREF_RT595_FACTORY_LOCK_FAILED;
    }
    return OPENREF_RT595_FACTORY_PROVISIONED;
}
