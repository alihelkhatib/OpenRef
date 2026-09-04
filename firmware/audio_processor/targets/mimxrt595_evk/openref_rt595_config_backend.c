#include "openref_rt595_config_backend.h"
#include <stddef.h>
#include <string.h>
static uint32_t address(const openref_rt595_config_backend_t *b,uint8_t s){return b->config_start+(uint32_t)s*b->sector_bytes;}
static bool read_slot(void *c,uint8_t s,uint8_t *r){openref_rt595_config_backend_t*b=c;return b&&s<2u&&r&&b->driver.read(b->driver.context,address(b,s),r,OPENREF_CONFIG_SLOT_BYTES);}
static bool write_slot(void *c,uint8_t s,const uint8_t*r){openref_rt595_config_backend_t*b=c;uint8_t page[256] __attribute__((aligned(4)));uint8_t verify[OPENREF_CONFIG_SLOT_BYTES] __attribute__((aligned(4)));if(!b||s>=2u||!r||b->page_bytes>sizeof(page))return false;memset(page,0xff,b->page_bytes);memcpy(page,r,OPENREF_CONFIG_SLOT_BYTES);uint32_t a=address(b,s);return b->driver.erase(b->driver.context,a,b->sector_bytes)&&b->driver.program(b->driver.context,a,page,b->page_bytes)&&b->driver.read(b->driver.context,a,verify,sizeof(verify))&&memcmp(r,verify,sizeof(verify))==0;}
bool openref_rt595_config_backend_init(openref_rt595_config_backend_t*b,openref_rt595_config_driver_t d,uint32_t fs,uint32_t fe,uint32_t pe,uint32_t cs,uint32_t ss,uint32_t ps){if(!b||!d.read||!d.erase||!d.program||fs>=fe||pe<fs||pe>cs||!ss||ps<OPENREF_CONFIG_SLOT_BYTES||ps>256u||ps>ss||cs%ss||cs%ps||ss%ps||cs<fs||cs>fe||ss>(fe-cs)/2u)return false;*b=(openref_rt595_config_backend_t){d,fs,fe,pe,cs,ss,ps};return true;}
openref_config_backend_t openref_rt595_config_backend(openref_rt595_config_backend_t*b){return(openref_config_backend_t){read_slot,write_slot,b};}
