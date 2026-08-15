#ifndef OPENREF_BOOT_COUNTER_H
#define OPENREF_BOOT_COUNTER_H

#include <stdbool.h>
#include <stdint.h>

typedef bool (*openref_boot_counter_read_fn)(
    void *context,
    uint32_t *value,
    bool *found);

typedef bool (*openref_boot_counter_write_fn)(
    void *context,
    uint32_t value);

bool openref_boot_counter_advance(
    openref_boot_counter_read_fn read_counter,
    openref_boot_counter_write_fn write_counter,
    void *context,
    uint32_t *active_boot_counter);

#endif
