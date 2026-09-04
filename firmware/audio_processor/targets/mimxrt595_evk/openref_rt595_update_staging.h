#ifndef OPENREF_RT595_UPDATE_STAGING_H
#define OPENREF_RT595_UPDATE_STAGING_H

#include <stdbool.h>
#include <stdint.h>
#include "openref_update_verifier.h"

#define OPENREF_RT595_UPDATE_MAX_PAGE_BYTES 512u
typedef bool (*openref_rt595_update_read_fn)(void *, uint32_t, uint8_t *, uint32_t);
typedef bool (*openref_rt595_update_erase_fn)(void *, uint32_t, uint32_t);
typedef bool (*openref_rt595_update_program_fn)(void *, uint32_t, const uint8_t *, uint32_t);
typedef struct { openref_rt595_update_read_fn read; openref_rt595_update_erase_fn erase; openref_rt595_update_program_fn program; void *context; } openref_rt595_update_flash_t;
typedef struct {
    openref_rt595_update_flash_t flash;
    openref_update_verifier_t *verifier;
    uint32_t manifest_base, base, capacity, sector_bytes, page_bytes, offset;
    uint16_t buffered;
    uint8_t page[OPENREF_RT595_UPDATE_MAX_PAGE_BYTES];
    uint32_t failures;
    bool active;
} openref_rt595_update_staging_t;

bool openref_rt595_update_staging_init(openref_rt595_update_staging_t *, openref_rt595_update_flash_t,
                                       uint32_t manifest_base, uint32_t image_base, uint32_t capacity,
                                       uint32_t sector_bytes, uint32_t page_bytes);
bool openref_rt595_update_staging_start(openref_rt595_update_staging_t *, openref_update_verifier_t *);
bool openref_rt595_update_staging_write(openref_rt595_update_staging_t *, const uint8_t *, uint32_t);
bool openref_rt595_update_staging_finish(openref_rt595_update_staging_t *);
void openref_rt595_update_staging_abort(openref_rt595_update_staging_t *);

/* `verified` proves the bytes read back during this staging transaction only.
 * A bootloader must independently authenticate the complete candidate slot
 * immediately before selection/execution and atomically enforce its own
 * confirmed-version rollback policy. Never treat this RAM flag as a durable
 * boot authorization record. */
#endif
