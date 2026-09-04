#include "openref_rt595_config_backend_mcux.h"
#include "fsl_cache.h"
#include <string.h>
#define RT595_FLASH_BASE 0x08000000u
#define RT595_FLASH_END 0x08200000u
static bool mcux_read(void*c,uint32_t a,void*d,uint32_t n){(void)c;if(a<RT595_FLASH_BASE||a>RT595_FLASH_END||n>RT595_FLASH_END-a)return false;memcpy(d,(const void *)(uintptr_t)a,n);return true;}
static bool mcux_erase(void*c,uint32_t a,uint32_t n){openref_rt595_config_mcux_t*m=c;if(a<RT595_FLASH_BASE)return false;bool ok=IAP_FlexspiNorErase(m->instance,m->config,a-RT595_FLASH_BASE,n)==kStatus_Success;if(ok)CACHE64_InvalidateCacheByRange(a,n);return ok;}
static bool mcux_program(void*c,uint32_t a,const void*d,uint32_t n){openref_rt595_config_mcux_t*m=c;if(a<RT595_FLASH_BASE||((uintptr_t)d&3u)!=0u||n!=m->config->pageSize)return false;bool ok=IAP_FlexspiNorPageProgram(m->instance,m->config,a-RT595_FLASH_BASE,(const uint32_t*)d)==kStatus_Success;if(ok)CACHE64_InvalidateCacheByRange(a,n);return ok;}
bool openref_rt595_config_mcux_init(openref_rt595_config_mcux_t*m,flexspi_nor_config_t*c,uint32_t instance,uint32_t protected_end,uint32_t config_start,uint32_t flash_end){if(!m||!c||instance!=0u||c->pageSize==0u||c->sectorSize==0u||flash_end!=RT595_FLASH_END)return false;m->config=c;m->instance=instance;openref_rt595_config_driver_t d={mcux_read,mcux_erase,mcux_program,m};return openref_rt595_config_backend_init(&m->backend,d,RT595_FLASH_BASE,flash_end,protected_end,config_start,c->sectorSize,c->pageSize);}
