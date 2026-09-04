#ifndef OPENREF_RT595_CONFIG_BACKEND_H
#define OPENREF_RT595_CONFIG_BACKEND_H
#include <stdbool.h>
#include <stdint.h>
#include "openref_config_store.h"
typedef bool (*openref_rt595_config_read_fn)(void *, uint32_t, void *, uint32_t);
typedef bool (*openref_rt595_config_erase_fn)(void *, uint32_t, uint32_t);
typedef bool (*openref_rt595_config_program_fn)(void *, uint32_t, const void *, uint32_t);
typedef struct { openref_rt595_config_read_fn read; openref_rt595_config_erase_fn erase; openref_rt595_config_program_fn program; void *context; } openref_rt595_config_driver_t;
typedef struct { openref_rt595_config_driver_t driver; uint32_t flash_start, flash_end, protected_end, config_start, sector_bytes, page_bytes; } openref_rt595_config_backend_t;
bool openref_rt595_config_backend_init(openref_rt595_config_backend_t *, openref_rt595_config_driver_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);
openref_config_backend_t openref_rt595_config_backend(openref_rt595_config_backend_t *);
#endif
