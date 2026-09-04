#include "openref_rt595_update_crypto.h"
#include <limits.h>
#include <stddef.h>
#include <string.h>
static void inc(uint32_t*v){if(*v!=UINT32_MAX)++*v;}
static bool nonzero(const uint8_t*p,uint32_t n){uint8_t v=0;while(n--)v|=*p++;return v!=0;}
static bool sig(void*c,const uint8_t d[80],const uint8_t id[8],const uint8_t s[64]){openref_rt595_update_crypto_t*x=c;uint8_t h[32];if(!x||!x->initialized||!d||!id||!s)return false;if(memcmp(id,x->key_id,8)!=0){inc(&x->rejected_keys);return false;}if(!x->driver.begin(x->driver.context)||!x->driver.update(x->driver.context,d,80)||!x->driver.finish(x->driver.context,h)||!x->driver.verify(x->driver.context,x->public_key,h,s)){inc(&x->failures);return false;}return true;}
static bool begin(void*c){openref_rt595_update_crypto_t*x=c;if(!x||!x->initialized||!x->driver.begin(x->driver.context)){if(x)inc(&x->failures);return false;}return true;}
static bool update(void*c,const uint8_t*d,uint32_t n){openref_rt595_update_crypto_t*x=c;if(!x||!x->initialized||!d||!n||!x->driver.update(x->driver.context,d,n)){if(x)inc(&x->failures);return false;}return true;}
static bool finish(void*c,uint8_t d[32]){openref_rt595_update_crypto_t*x=c;if(!x||!x->initialized||!d||!x->driver.finish(x->driver.context,d)){if(x)inc(&x->failures);return false;}return true;}
bool openref_rt595_update_crypto_init(openref_rt595_update_crypto_t*x,openref_rt595_update_crypto_driver_t d,const uint8_t id[8],const uint8_t pk[64]){if(!x||!d.begin||!d.update||!d.finish||!d.verify||!id||!pk||!nonzero(id,8)||!nonzero(pk,64))return false;memset(x,0,sizeof(*x));x->driver=d;memcpy(x->key_id,id,8);memcpy(x->public_key,pk,64);x->initialized=true;return true;}
openref_update_crypto_t openref_rt595_update_crypto_callbacks(openref_rt595_update_crypto_t*x){openref_update_crypto_t c={sig,begin,update,finish,x};return c;}
