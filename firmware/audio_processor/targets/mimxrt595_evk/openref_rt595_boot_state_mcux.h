#ifndef OPENREF_RT595_BOOT_STATE_MCUX_H
#define OPENREF_RT595_BOOT_STATE_MCUX_H
#include "fsl_iap.h"
#include "openref_rt595_boot_state.h"
#include "openref_rt595_config_backend_mcux.h"
typedef struct {openref_rt595_config_mcux_t flash;openref_rt595_boot_state_store_t store;} openref_rt595_boot_state_mcux_t;
bool openref_rt595_boot_state_mcux_init(openref_rt595_boot_state_mcux_t *,flexspi_nor_config_t *,uint32_t,uint32_t,uint32_t,uint32_t);
#endif
