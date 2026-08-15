#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "openref_boot_counter.h"

typedef struct {
    uint32_t value;
    bool found;
    bool read_ok;
    bool write_ok;
    bool corrupt_after_write;
} storage_probe_t;

static bool probe_read(void *context, uint32_t *value, bool *found)
{
    storage_probe_t *probe = context;
    if (!probe->read_ok) {
        return false;
    }
    *value = probe->value;
    *found = probe->found;
    return true;
}

static bool probe_write(void *context, uint32_t value)
{
    storage_probe_t *probe = context;
    if (!probe->write_ok) {
        return false;
    }
    probe->value = probe->corrupt_after_write ? value + 1u : value;
    probe->found = true;
    return true;
}

int main(void)
{
    uint32_t active = 0u;
    storage_probe_t fresh = {.read_ok = true, .write_ok = true};
    assert(openref_boot_counter_advance(probe_read, probe_write, &fresh, &active));
    assert(active == 1u);
    assert(openref_boot_counter_advance(probe_read, probe_write, &fresh, &active));
    assert(active == 2u);

    storage_probe_t exhausted = {
        .value = UINT32_MAX, .found = true, .read_ok = true, .write_ok = true,
    };
    assert(!openref_boot_counter_advance(
        probe_read, probe_write, &exhausted, &active));

    storage_probe_t write_failure = {.read_ok = true};
    assert(!openref_boot_counter_advance(
        probe_read, probe_write, &write_failure, &active));

    storage_probe_t verify_failure = {
        .read_ok = true, .write_ok = true, .corrupt_after_write = true,
    };
    assert(!openref_boot_counter_advance(
        probe_read, probe_write, &verify_failure, &active));
    return 0;
}
