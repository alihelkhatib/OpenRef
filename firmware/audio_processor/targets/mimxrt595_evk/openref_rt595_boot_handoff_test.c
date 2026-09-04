#include "openref_rt595_boot_handoff.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

typedef struct { uint8_t vector[8]; bool read_ok; } image_t;
static void word(uint8_t *p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);p[2]=(uint8_t)(v>>16);p[3]=(uint8_t)(v>>24);}
static bool read_vector(void *c,uint32_t a,uint8_t*d,uint32_t n){image_t*i=c;(void)a;if(!i->read_ok||n!=8u)return false;memcpy(d,i->vector,n);return true;}
static openref_rt595_boot_handoff_layout_t layout(void){openref_rt595_boot_handoff_layout_t l={true,0x08101000u,0x00020000u,0x20000000u,0x00040000u,128u};return l;}
static bool prepare(image_t*i,openref_rt595_boot_handoff_layout_t*l,openref_rt595_boot_handoff_plan_t*p){openref_rt595_boot_vector_reader_t r={read_vector,i};return openref_rt595_boot_handoff_prepare(r,l,p);}

enum {DISABLE=1,STOP,CLEAR,DCACHE,ICACHE,VTOR,SYNC,MSP,BRANCH,FAIL};
typedef struct {int log[16],count,fail_at;uint32_t vtor,msp,reset;} trace_t;
static bool step(trace_t*t,int event){t->log[t->count++]=event;return t->fail_at!=event;}
static bool disable(void*c){return step(c,DISABLE);} static bool stop(void*c){return step(c,STOP);}
static bool clear(void*c){return step(c,CLEAR);} static bool dc(void*c){return step(c,DCACHE);}
static bool ic(void*c){return step(c,ICACHE);} static bool sync_(void*c){return step(c,SYNC);}
static bool fail(void*c){return step(c,FAIL);}
static bool vtor(void*c,uint32_t v){trace_t*t=c;t->vtor=v;return step(t,VTOR);}
static bool msp(void*c,uint32_t v){trace_t*t=c;t->msp=v;return step(t,MSP);}
static bool branch(void*c,uint32_t v){trace_t*t=c;t->reset=v;return step(t,BRANCH);}
static openref_rt595_boot_handoff_ops_t ops(trace_t*t){openref_rt595_boot_handoff_ops_t o={disable,stop,clear,dc,ic,vtor,sync_,msp,branch,fail,t};return o;}

int main(void){
 image_t i={{0},true};openref_rt595_boot_handoff_layout_t l=layout();openref_rt595_boot_handoff_plan_t p;
 word(i.vector,0x20040000u);word(i.vector+4,0x08101101u);assert(prepare(&i,&l,&p));assert(p.vector_table==l.image_base&&p.initial_msp==0x20040000u&&p.reset_handler==0x08101101u);
 l.authenticated=false;assert(!prepare(&i,&l,&p)&&p.vector_table==0u);l.authenticated=true;
 word(i.vector,0x20000000u);assert(!prepare(&i,&l,&p)&&p.vector_table==0u);
 word(i.vector,0x20000004u);assert(!prepare(&i,&l,&p));
 word(i.vector,0x20040008u);assert(!prepare(&i,&l,&p));
 word(i.vector,0x20001000u);word(i.vector+4,0x08101100u);assert(!prepare(&i,&l,&p));
 word(i.vector+4,0x08101005u);assert(!prepare(&i,&l,&p));
 word(i.vector+4,0x08121001u);assert(!prepare(&i,&l,&p));
 word(i.vector+4,0x08101101u);i.read_ok=false;assert(!prepare(&i,&l,&p));i.read_ok=true;
 l.image_base++;assert(!prepare(&i,&l,&p));l=layout();l.vtor_alignment=96u;assert(!prepare(&i,&l,&p));
 l=layout();l.image_base=0xfffff000u;l.image_size=0x2000u;assert(!prepare(&i,&l,&p));
 l=layout();l.ram_base=0xfffff000u;l.ram_size=0x2000u;assert(!prepare(&i,&l,&p));
 l=layout();assert(prepare(&i,&l,&p));trace_t t={{0},0,0,0,0,0};openref_rt595_boot_handoff_ops_t o=ops(&t);assert(!openref_rt595_boot_handoff_execute(&p,&o));
 {int expected[]={DISABLE,STOP,CLEAR,DCACHE,ICACHE,VTOR,SYNC,MSP,BRANCH,FAIL};assert(t.count==10);assert(memcmp(t.log,expected,sizeof(expected))==0);assert(t.vtor==p.vector_table&&t.msp==p.initial_msp&&t.reset==p.reset_handler);}
 memset(&t,0,sizeof(t));t.fail_at=CLEAR;o=ops(&t);assert(!openref_rt595_boot_handoff_execute(&p,&o));assert(t.count==4&&t.log[0]==DISABLE&&t.log[1]==STOP&&t.log[2]==CLEAR&&t.log[3]==FAIL);
 memset(&t,0,sizeof(t));o=ops(&t);o.set_msp=NULL;assert(!openref_rt595_boot_handoff_execute(&p,&o));assert(t.count==0);
 memset(&t,0,sizeof(t));o=ops(&t);p.reset_handler&=~1u;assert(!openref_rt595_boot_handoff_execute(&p,&o));assert(t.count==1&&t.log[0]==FAIL);
 return 0;
}
