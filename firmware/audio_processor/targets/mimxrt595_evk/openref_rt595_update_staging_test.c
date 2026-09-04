#include "openref_rt595_update_staging.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {uint8_t mem[2048];unsigned erase,program;uint32_t last_program_address;bool corrupt;} fake_t;
static bool rd(void*c,uint32_t a,uint8_t*d,uint32_t n){fake_t*f=c;memcpy(d,&f->mem[a],n);if(f->corrupt)d[0]^=1;return true;}
static bool er(void*c,uint32_t a,uint32_t n){fake_t*f=c;memset(&f->mem[a],0xff,n);++f->erase;return true;}
static bool pg(void*c,uint32_t a,const uint8_t*d,uint32_t n){fake_t*f=c;memcpy(&f->mem[a],d,n);++f->program;f->last_program_address=a;return true;}
static bool hu(void*c,const uint8_t*d,uint32_t n){(void)c;(void)d;(void)n;return true;}
static bool hf(void*c,uint8_t*d){(void)c;memset(d,0,OPENREF_UPDATE_DIGEST_BYTES);return true;}
static openref_update_verifier_t verifier(uint32_t size){openref_update_verifier_t v={0};v.active=true;v.manifest.image_size=size;v.crypto.hash_update=hu;v.crypto.hash_finish=hf;return v;}
int main(void){fake_t f={0};openref_rt595_update_staging_t s;openref_rt595_update_flash_t ops={rd,er,pg,&f};uint8_t data[300];memset(data,0xa5,sizeof(data));
 assert(!openref_rt595_update_staging_init(&s,ops,1,512,1024,512,256));
 assert(openref_rt595_update_staging_init(&s,ops,0,512,1024,512,256));openref_update_verifier_t v=verifier(sizeof(data));v.manifest_wire[0]=0x4fu;
 assert(openref_rt595_update_staging_start(&s,&v)&&f.erase==2);assert(!openref_rt595_update_staging_start(&s,&v));assert(openref_rt595_update_staging_write(&s,data,100));assert(v.received_bytes==0u);assert(openref_rt595_update_staging_write(&s,&data[100],200));assert(v.received_bytes==256u);assert(openref_rt595_update_staging_finish(&s));assert(v.verified&&f.program==3&&f.last_program_address==0u);assert(memcmp(&f.mem[512],data,sizeof(data))==0);assert(f.mem[812]==0xff);assert(memcmp(f.mem,v.manifest_wire,OPENREF_UPDATE_MANIFEST_BYTES)==0&&f.mem[OPENREF_UPDATE_MANIFEST_BYTES]==0xff);
 v=verifier(10);f.corrupt=true;assert(openref_rt595_update_staging_start(&s,&v));assert(openref_rt595_update_staging_write(&s,data,10));assert(!openref_rt595_update_staging_finish(&s)&&!s.active&&!v.verified&&s.failures==1);
 v=verifier(10);assert(openref_rt595_update_staging_start(&s,&v));openref_rt595_update_staging_abort(&s);assert(!s.active&&!v.active&&!v.verified);
 puts("openref_rt595_update_staging_test: PASS");return 0;}
