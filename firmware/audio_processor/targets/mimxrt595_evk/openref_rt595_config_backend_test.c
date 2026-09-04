#include <assert.h>
#include <string.h>
#include "openref_rt595_config_backend.h"
#define BASE 0x08000000u
#define START 0x081fe000u
#define SECTOR 4096u
typedef struct { uint8_t data[SECTOR*2u]; uint32_t erased,programmed,length; bool corrupt; } fake_t;
static bool range(uint32_t a,uint32_t n){return a>=START&&(a-START)<=SECTOR*2u&&n<=SECTOR*2u-(a-START);}
static bool rd(void*c,uint32_t a,void*d,uint32_t n){fake_t*f=c;if(!range(a,n))return false;memcpy(d,f->data+(a-START),n);if(f->corrupt)((uint8_t*)d)[0]^=1u;return true;}
static bool er(void*c,uint32_t a,uint32_t n){fake_t*f=c;if(n!=SECTOR||!range(a,n))return false;memset(f->data+(a-START),0xff,n);f->erased=a;return true;}
static bool pg(void*c,uint32_t a,const void*d,uint32_t n){fake_t*f=c;if(a%256u||n!=256u||!range(a,n))return false;memcpy(f->data+(a-START),d,n);f->programmed=a;f->length=n;return true;}
int main(void){fake_t f;memset(&f,0,sizeof(f));memset(f.data,0xff,sizeof(f.data));openref_rt595_config_driver_t d={rd,er,pg,&f};openref_rt595_config_backend_t b;
assert(!openref_rt595_config_backend_init(&b,d,BASE,0x08200000u,START+1u,START,SECTOR,256u));
assert(!openref_rt595_config_backend_init(&b,d,BASE,0x08200000u,0x08040000u,START+1u,SECTOR,256u));
assert(openref_rt595_config_backend_init(&b,d,BASE,0x08200000u,0x08040000u,START,SECTOR,256u));
openref_config_backend_t x=openref_rt595_config_backend(&b);uint8_t in[OPENREF_CONFIG_SLOT_BYTES],out[OPENREF_CONFIG_SLOT_BYTES];memset(in,0xa5,sizeof(in));
assert(x.write_slot(x.context,1u,in));assert(f.erased==START+SECTOR&&f.programmed==f.erased&&f.length==256u);assert(x.read_slot(x.context,1u,out)&&memcmp(in,out,sizeof(in))==0);assert(f.data[SECTOR+255u]==0xffu);f.corrupt=true;assert(!x.write_slot(x.context,0u,in));assert(!x.read_slot(x.context,2u,out));return 0;}
