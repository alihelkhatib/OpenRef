#include "openref_rt595_update_delivery.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t flash[1536];
    uint8_t sum;
    uint32_t erases;
    bool signature_ok;
    bool activate_ok;
} fake_t;

static void put32(uint8_t *p, uint32_t v)
{
    p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);p[2]=(uint8_t)(v>>16);p[3]=(uint8_t)(v>>24);
}
static bool rd(void *c,uint32_t a,uint8_t *p,uint32_t n){fake_t*f=c;if(a>sizeof(f->flash)||n>sizeof(f->flash)-a)return false;memcpy(p,f->flash+a,n);return true;}
static bool er(void *c,uint32_t a,uint32_t n){fake_t*f=c;if(a>sizeof(f->flash)||n>sizeof(f->flash)-a)return false;memset(f->flash+a,0xff,n);++f->erases;return true;}
static bool pg(void *c,uint32_t a,const uint8_t*p,uint32_t n){fake_t*f=c;if(a>sizeof(f->flash)||n>sizeof(f->flash)-a)return false;for(uint32_t i=0;i<n;i++)f->flash[a+i]&=p[i];return true;}
static bool sig(void*c,const uint8_t d[80],const uint8_t k[8],const uint8_t s[64]){(void)d;(void)k;(void)s;return ((fake_t*)c)->signature_ok;}
static bool hb(void*c){((fake_t*)c)->sum=0;return true;}
static bool hu(void*c,const uint8_t*p,uint32_t n){fake_t*f=c;while(n--)f->sum=(uint8_t)(f->sum+*p++);return true;}
static bool hf(void*c,uint8_t*d){memset(d,0,32);d[0]=((fake_t*)c)->sum;return true;}
static bool activate(void*c,uint8_t slot,uint32_t version){return ((fake_t*)c)->activate_ok&&slot==1u&&version==8u;}

static void manifest(uint8_t *m,const uint8_t *image,uint32_t n)
{
    uint8_t sum=0;for(uint32_t i=0;i<n;i++)sum=(uint8_t)(sum+image[i]);
    memset(m,0,OPENREF_UPDATE_MANIFEST_BYTES);memcpy(m,"ORUP",4);m[4]=1;m[5]=OPENREF_UPDATE_TARGET_AUDIO;
    put32(m+8,0x595u);put32(m+12,8);put32(m+16,2);put32(m+20,n);m[24]=sum;
    memset(m+56,0x55,16);memset(m+72,0x77,8);m[80]=1;
}

static openref_rt595_update_delivery_t setup(fake_t*f,openref_rt595_update_staging_t*s)
{
    openref_rt595_update_flash_t flash={rd,er,pg,f};
    assert(openref_rt595_update_staging_init(&s[0],flash,0,256,512,256,256));
    assert(openref_rt595_update_staging_init(&s[1],flash,768,1024,512,256,256));
    openref_update_platform_t p={OPENREF_UPDATE_TARGET_AUDIO,0x595u,3,1,7,512};
    openref_update_crypto_t c={sig,hb,hu,hf,f};openref_rt595_update_delivery_t d;
    assert(openref_rt595_update_delivery_init(&d,&s[0],&s[1],0,256,512,100,&p,c,activate,f));
    return d;
}

int main(void)
{
    fake_t f={.signature_ok=true,.activate_ok=true};memset(f.flash,0xff,sizeof(f.flash));
    openref_rt595_update_staging_t s[2];openref_rt595_update_delivery_t d=setup(&f,s);
    uint8_t image[300],m[144];memset(image,0xa5,sizeof(image));manifest(m,image,sizeof(image));

    /* The running slot and unauthenticated manifests never cause an erase. */
    assert(openref_rt595_update_delivery_begin(&d,1,0,m,0)==OPENREF_RT595_UPDATE_DELIVERY_REJECTED);
    assert(f.erases==0);f.signature_ok=false;
    assert(openref_rt595_update_delivery_begin(&d,1,1,m,0)==OPENREF_RT595_UPDATE_DELIVERY_AUTH_FAILED);
    assert(f.erases==0);f.signature_ok=true;

    assert(openref_rt595_update_delivery_begin(&d,1,1,m,0)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(f.erases==2 && f.flash[768]==0xff); /* manifest invalidated first */
    assert(openref_rt595_update_delivery_chunk(&d,1,0,0,image,128,10)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(openref_rt595_update_delivery_chunk(&d,1,1,128,image+128,172,20)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(openref_rt595_update_delivery_finish(&d,1,2,30)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(d.completed && memcmp(f.flash+1024,image,sizeof(image))==0);
    assert(memcmp(f.flash+768,m,sizeof(m))==0); /* signed commit is last */
    assert(openref_rt595_update_delivery_begin(&d,1,1,m,40)==OPENREF_RT595_UPDATE_DELIVERY_REJECTED);

    /* A duplicated/out-of-order chunk poisons only that reserved session. */
    assert(openref_rt595_update_delivery_begin(&d,2,1,m,50)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(openref_rt595_update_delivery_chunk(&d,2,1,0,image,10,51)==OPENREF_RT595_UPDATE_DELIVERY_PROTOCOL_FAILED);
    assert(!d.active && openref_rt595_update_delivery_begin(&d,2,1,m,52)==OPENREF_RT595_UPDATE_DELIVERY_REJECTED);

    assert(openref_rt595_update_delivery_begin(&d,3,1,m,UINT32_MAX-20u)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(openref_rt595_update_delivery_poll(&d,90u)); /* wrap-safe elapsed 111 */
    assert(!d.active);
    assert(openref_rt595_update_delivery_begin(&d,4,1,m,100)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    openref_rt595_update_delivery_reset(&d);
    assert(!d.active && openref_rt595_update_delivery_begin(&d,4,1,m,101)==OPENREF_RT595_UPDATE_DELIVERY_REJECTED);

    /* A durable image whose boot-state activation fails stays unselected. */
    f.activate_ok=false;
    assert(openref_rt595_update_delivery_begin(&d,5,1,m,200)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(openref_rt595_update_delivery_chunk(&d,5,0,0,image,sizeof(image),201)==OPENREF_RT595_UPDATE_DELIVERY_OK);
    assert(openref_rt595_update_delivery_finish(&d,5,1,202)==OPENREF_RT595_UPDATE_DELIVERY_STORAGE_FAILED);
    assert(!d.active && !d.completed && memcmp(f.flash+768,m,sizeof(m))==0);

    puts("openref_rt595_update_delivery_test: PASS");
    return 0;
}
