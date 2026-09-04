#ifndef OPENREF_RT595_UPDATE_STAGING_MCUX_H
#define OPENREF_RT595_UPDATE_STAGING_MCUX_H
#include "fsl_iap.h"
#include "openref_rt595_update_staging.h"
typedef struct { openref_rt595_update_staging_t staging; flexspi_nor_config_t *config; uint32_t instance; } openref_rt595_update_staging_mcux_t;
bool openref_rt595_update_staging_mcux_init(openref_rt595_update_staging_mcux_t *, uint32_t instance,
 flexspi_nor_config_t *, uint32_t flash_bytes, uint32_t manifest_base, uint32_t image_base, uint32_t capacity);
#endif
