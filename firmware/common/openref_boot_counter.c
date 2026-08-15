#include "openref_boot_counter.h"

#include <stddef.h>

bool openref_boot_counter_advance(
    openref_boot_counter_read_fn read_counter,
    openref_boot_counter_write_fn write_counter,
    void *context,
    uint32_t *active_boot_counter)
{
    if (read_counter == NULL || write_counter == NULL ||
        active_boot_counter == NULL) {
        return false;
    }
    uint32_t previous = 0u;
    bool found = false;
    if (!read_counter(context, &previous, &found) ||
        (found && previous == UINT32_MAX)) {
        return false;
    }
    uint32_t next = found ? previous + 1u : 1u;
    if (!write_counter(context, next)) {
        return false;
    }
    uint32_t verified = 0u;
    bool verify_found = false;
    if (!read_counter(context, &verified, &verify_found) ||
        !verify_found || verified != next) {
        return false;
    }
    *active_boot_counter = next;
    return true;
}
