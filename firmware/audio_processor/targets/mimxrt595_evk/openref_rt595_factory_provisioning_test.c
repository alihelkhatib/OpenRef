#include "openref_rt595_factory_provisioning.h"
#include <assert.h>
#include <string.h>
typedef struct{bool auth,locked,io,fail_write,fail_verify,fail_lock;openref_rt595_factory_probe_t s[3];uint8_t writes[3],order[4],n;}fake_t;
static bool auth(void*c){return((fake_t*)c)->auth;}static bool getlock(void*c,bool*l){fake_t*f=c;if(f->io)return false;*l=f->locked;return true;}
static openref_rt595_factory_probe_t probe(void*c,openref_rt595_factory_region_t r,const uint8_t*b,uint32_t n){(void)b;(void)n;fake_t*f=c;return f->io?OPENREF_RT595_FACTORY_PROBE_IO:f->s[r];}
static bool program(void*c,openref_rt595_factory_region_t r,const uint8_t*b,uint32_t n){(void)b;(void)n;fake_t*f=c;f->writes[r]++;f->order[f->n++]=(uint8_t)r;return!f->fail_write;}
static bool verify(void*c,openref_rt595_factory_region_t r,const uint8_t*b,uint32_t n){(void)r;(void)b;(void)n;return!((fake_t*)c)->fail_verify;}
static bool setlock(void*c){fake_t*f=c;f->order[f->n++]=3;if(f->fail_lock)return false;f->locked=true;return true;}
static openref_rt595_factory_driver_t driver(fake_t*f){return(openref_rt595_factory_driver_t){auth,getlock,probe,program,verify,setlock,f};}
static openref_rt595_factory_plan_t plan(void){static const uint8_t a[]={1},b[]={2},c[]={3};return(openref_rt595_factory_plan_t){{{a,1},{b,1},{c,1}}};}
static fake_t blank(void){fake_t f={0};f.auth=true;for(int i=0;i<3;i++)f.s[i]=OPENREF_RT595_FACTORY_PROBE_BLANK;return f;}
int main(void){openref_rt595_factory_plan_t p=plan();fake_t f=blank();openref_rt595_factory_driver_t d=driver(&f);
 assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_PROVISIONED);assert(f.locked&&f.n==4&&!memcmp(f.order,(uint8_t[]){0,1,2,3},4));
 f=blank();f.auth=false;d=driver(&f);assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_UNAUTHORIZED&&f.n==0);
 f=blank();f.s[1]=OPENREF_RT595_FACTORY_PROBE_CORRUPT;d=driver(&f);assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_NONBLANK&&f.n==0);
 f=blank();f.s[0]=OPENREF_RT595_FACTORY_PROBE_MATCH;d=driver(&f);assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_PROVISIONED&&f.writes[0]==0&&f.writes[1]==1&&f.writes[2]==1);
 f=blank();f.locked=true;for(int i=0;i<3;i++)f.s[i]=OPENREF_RT595_FACTORY_PROBE_MATCH;d=driver(&f);assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_ALREADY_PROVISIONED&&f.n==0);f.s[2]=OPENREF_RT595_FACTORY_PROBE_BLANK;assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_LOCKED_MISMATCH);
 f=blank();f.fail_verify=true;d=driver(&f);assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_VERIFY_FAILED&&!f.locked);
 f=blank();f.fail_lock=true;d=driver(&f);assert(openref_rt595_factory_provision(&d,&p)==OPENREF_RT595_FACTORY_LOCK_FAILED&&!f.locked);return 0;}
