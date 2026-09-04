#include "openref_rt595_boot_state.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct{uint8_t slot[2][OPENREF_CONFIG_SLOT_BYTES];bool fail_write,corrupt;}fake_t;
static bool rd(void*c,uint8_t s,uint8_t*r){fake_t*f=c;if(s>1)return false;memcpy(r,f->slot[s],sizeof(f->slot[s]));return true;}
static bool wr(void*c,uint8_t s,const uint8_t*r){fake_t*f=c;if(s>1||f->fail_write)return false;memcpy(f->slot[s],r,sizeof(f->slot[s]));if(f->corrupt)f->slot[s][20]^=1u;return true;}
static openref_config_backend_t backend(fake_t*f){return(openref_config_backend_t){rd,wr,f};}
int main(void){fake_t f;memset(&f,0xff,sizeof(f));f.fail_write=false;f.corrupt=false;openref_rt595_boot_state_store_t b;assert(openref_rt595_boot_state_init(&b,backend(&f)));assert(!openref_rt595_boot_state_load(&b));assert(openref_rt595_boot_state_initialize(&b,0u,10u));openref_boot_slot_t slots[2]={{true,true,10u},{true,true,11u}};assert(openref_rt595_boot_state_stage(&b,1u,slots));openref_boot_decision_t d=openref_rt595_boot_state_select(&b,slots,2u);assert(d.kind==OPENREF_BOOT_DECISION_TRIAL&&d.slot==1u&&b.state.pending_attempts==1u);openref_rt595_boot_state_store_t reboot;assert(openref_rt595_boot_state_init(&reboot,backend(&f)));assert(openref_rt595_boot_state_load(&reboot)&&reboot.state.pending_attempts==1u);f.fail_write=true;d=openref_rt595_boot_state_select(&reboot,slots,2u);assert(d.kind==OPENREF_BOOT_DECISION_NONE&&reboot.state.pending_attempts==1u);f.fail_write=false;f.corrupt=true;assert(!openref_rt595_boot_state_confirm(&reboot,1u,slots));assert(reboot.state.confirmed_slot==0u);f.corrupt=false;assert(openref_rt595_boot_state_load(&reboot));assert(reboot.state.confirmed_slot==0u);puts("openref_rt595_boot_state_test: PASS");return 0;}
