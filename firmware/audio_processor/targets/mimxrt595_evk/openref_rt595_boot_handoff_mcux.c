#include "openref_rt595_boot_handoff_mcux.h"
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include "fsl_common.h"
#include "fsl_cache.h"
static bool xip_read(void*c,uint32_t a,uint8_t*d,uint32_t n){(void)c;if(!d||n==0u)return false;memcpy(d,(const void *)(uintptr_t)a,n);return true;}
bool openref_rt595_boot_handoff_mcux_prepare(const openref_rt595_boot_handoff_layout_t*l,openref_rt595_boot_handoff_plan_t*p){const openref_rt595_boot_vector_reader_t r={xip_read,NULL};return openref_rt595_boot_handoff_prepare(r,l,p);}
static void fail_closed(void)__attribute__((noreturn));
static void fail_closed(void){__disable_irq();SysTick->CTRL=0u;for(;;){__DSB();__WFI();}}
void openref_rt595_boot_handoff_mcux_execute(const openref_rt595_boot_handoff_plan_t*p){uint32_t count,index;if(!p||p->vector_table==0u||p->initial_msp==0u||(p->reset_handler&1u)==0u)fail_closed();__disable_irq();SysTick->CTRL=0u;SysTick->LOAD=0u;SysTick->VAL=0u;count=(SCnSCB->ICTR&SCnSCB_ICTR_INTLINESNUM_Msk)+1u;if(count>16u)fail_closed();for(index=0u;index<count;++index){NVIC->ICER[index]=UINT32_MAX;NVIC->ICPR[index]=UINT32_MAX;}SCB->ICSR=SCB_ICSR_PENDSTCLR_Msk|SCB_ICSR_PENDSVCLR_Msk;CACHE64_CleanCache(CACHE64_CTRL0);CACHE64_CleanCache(CACHE64_CTRL1);CACHE64_DisableCache(CACHE64_CTRL0);CACHE64_DisableCache(CACHE64_CTRL1);SCB->VTOR=p->vector_table;__DSB();__ISB();
/* Never return through a C frame after changing MSP. */
__asm volatile("msr msp, %0\n dsb\n isb\n bx %1\n"::"r"(p->initial_msp),"r"(p->reset_handler):"memory");fail_closed();}
