#ifndef OPENREF_RT595_CONFIG_BACKEND_MCUX_H
#define OPENREF_RT595_CONFIG_BACKEND_MCUX_H
#include "openref_rt595_config_backend.h"
#include "fsl_iap.h"
typedef struct { openref_rt595_config_backend_t backend; flexspi_nor_config_t *config; uint32_t instance; } openref_rt595_config_mcux_t;
bool openref_rt595_config_mcux_init(openref_rt595_config_mcux_t *, flexspi_nor_config_t *, uint32_t, uint32_t, uint32_t, uint32_t);
#endif
