#include "openref_rt595_app_confirmation.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct { uint8_t page[2][OPENREF_CONFIG_SLOT_BYTES]; bool fail_write; } fake_t;
static bool rd(void *c,uint8_t s,uint8_t *p){fake_t*f=c;if(s>1u)return false;memcpy(p,f->page[s],sizeof(f->page[s]));return true;}
static bool wr(void *c,uint8_t s,const uint8_t *p){fake_t*f=c;if(s>1u||f->fail_write)return false;memcpy(f->page[s],p,sizeof(f->page[s]));return true;}
static openref_config_backend_t backend(fake_t*f){return(openref_config_backend_t){rd,wr,f};}
static openref_rt595_app_health_t healthy(void){return(openref_rt595_app_health_t){true,true,true,true,true,true};}

int main(void)
{
    fake_t f; openref_rt595_boot_state_store_t b; openref_rt595_app_confirmation_t s;
    openref_boot_slot_t slots[2]={{true,true,10u},{true,true,11u}}; uint32_t now=0u;
    memset(&f,0xff,sizeof(f)); f.fail_write=false;
    assert(openref_rt595_boot_state_init(&b,backend(&f)));
    assert(openref_rt595_boot_state_initialize(&b,0u,10u));
    assert(openref_rt595_boot_state_stage(&b,1u,slots));
    assert(openref_rt595_boot_state_select(&b,slots,3u).kind==OPENREF_BOOT_DECISION_TRIAL);
    assert(openref_rt595_app_confirmation_init(&s,&b,1u,slots));

    /* Every required health source independently breaks continuity. */
    for(unsigned which=0u;which<6u;which++) {
        openref_rt595_app_health_t bad=healthy();
        now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
        if(which==0u)bad.clocks_ok=false;
        if(which==1u)bad.storage_ok=false;
        if(which==2u)bad.watchdog_ok=false;
        if(which==3u)bad.audio_ok=false;
        if(which==4u)bad.peer_ok=false;
        if(which==5u)bad.fault_free=false;
        now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,bad,now));
        assert(s.healthy_samples==0u);
    }
    now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    assert(s.healthy_samples==1u);
    /* Reset is represented by a fresh RAM supervisor; soak is not persisted. */
    assert(openref_rt595_app_confirmation_init(&s,&b,1u,slots));
    assert(s.healthy_samples==0u);
    now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    now+=30u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    assert(s.healthy_samples==0u && !s.sample_time_valid);
    now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    assert(s.healthy_samples==0u && !s.sample_time_valid);

    for(uint32_t i=0;i<OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES-1u;i++) {
        now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    }
    openref_rt595_app_health_t bad=healthy(); bad.peer_ok=false;
    now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,bad,now));
    assert(s.healthy_samples==0u && b.state.confirmed_slot==0u);
    for(uint32_t i=0;i<OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES-1u;i++) {
        now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    }
    openref_rt595_app_confirmation_fault(&s);
    assert(s.healthy_samples==0u);

    for(uint32_t i=0;i<OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES-1u;i++) {
        now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    }
    f.fail_write=true;
    now+=10u; assert(!openref_rt595_app_confirmation_observe(&s,healthy(),now));
    assert(s.status==OPENREF_RT595_CONFIRMATION_PERSIST_FAILED);
    assert(s.persistence_failures==1u && s.healthy_samples==0u);
    assert(b.state.confirmed_slot==0u && b.state.pending_slot==1u);
    f.fail_write=false;
    for(uint32_t i=0;i<OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES;i++) {
        now+=10u; assert(openref_rt595_app_confirmation_observe(&s,healthy(),now) ==
               (i+1u==OPENREF_RT595_CONFIRMATION_SOAK_SAMPLES));
    }
    assert(s.status==OPENREF_RT595_CONFIRMATION_CONFIRMED);
    assert(b.state.confirmed_slot==1u && b.state.pending_slot==OPENREF_BOOT_NO_SLOT);

    assert(!openref_rt595_app_confirmation_init(&s,&b,1u,slots));
    assert(!openref_rt595_app_confirmation_init(&s,&b,0u,slots));
    puts("openref_rt595_app_confirmation_test: PASS");
    return 0;
}
