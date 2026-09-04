#include "openref_rt595_boot_state_mcux.h"
#include <stddef.h>
bool openref_rt595_boot_state_mcux_init(openref_rt595_boot_state_mcux_t*b,flexspi_nor_config_t*c,uint32_t instance,uint32_t protected_end,uint32_t state_start,uint32_t flash_end){if(!b||!c||state_start<protected_end)return false;if(!openref_rt595_config_mcux_init(&b->flash,c,instance,protected_end,state_start,flash_end))return false;return openref_rt595_boot_state_init(&b->store,openref_rt595_config_backend(&b->flash.backend));}
