#include "openref_rt595_bootstrap.h"

#include <assert.h>
#include <string.h>

/* The coordinator has its own exhaustive authentication/state tests. Here we
 * exercise the bootstrap's final fail-closed boundary with a deliberately
 * invalid coordinator and verify that no prepare or transfer can occur. */
static unsigned prepared, transferred, recovered, statuses;
static openref_rt595_bootstrap_recovery_reason_t reason;
static openref_rt595_boot_handoff_layout_t seen;
static bool prep(void *c,const openref_rt595_boot_handoff_layout_t*l,openref_rt595_boot_handoff_plan_t*p){(void)c;seen=*l;p->vector_table=l->image_base;p->initial_msp=l->ram_base+0x100u;p->reset_handler=l->image_base+0x101u;++prepared;return true;}
static void jump(void*c,const openref_rt595_boot_handoff_plan_t*p){(void)c;(void)p;++transferred;}
static void recover(void*c){(void)c;++recovered;}
static void status(void*c,openref_rt595_bootstrap_recovery_reason_t r){(void)c;reason=r;++statuses;}
static bool never_read(void*c,uint32_t a,uint8_t*d,uint32_t n){(void)c;(void)a;(void)d;(void)n;return false;}
int main(void)
{
    openref_rt595_boot_state_store_t state_store = {0};
    openref_rt595_boot_coordinator_t coordinator = {.state_store=&state_store};
    openref_rt595_bootstrap_t bootstrap = {
        .coordinator=&coordinator,.image_base={0x08041000u,0x08101000u},
        .image_capacity={0xbf000u,0xbf000u},.ram_base=0x20000000u,
        .authenticated_image_size={0x1000u,0x2000u},
        .ram_size=0x00400000u,.vtor_alignment=128u,.prepare=prep,
        .transfer=jump,.recovery=recover,.status=status
    };
    assert(!openref_rt595_bootstrap_run(&bootstrap));
    assert(prepared==0u && transferred==0u && recovered==1u);
    assert(statuses==1u && reason==OPENREF_RT595_BOOTSTRAP_RECOVERY_DURABLE_STATE);
    {
        const openref_boot_slot_t slots[2]={{true,true,7u},{true,true,8u}};
        const openref_boot_decision_t decision={OPENREF_BOOT_SLOT_B,OPENREF_BOOT_DECISION_TRIAL,true};
        bootstrap.authenticated_image_size[1]=0x2000u;
        assert(!openref_rt595_bootstrap_handoff(&bootstrap,&decision,slots));
        assert(prepared==1u && transferred==1u && recovered==2u);
        assert(reason==OPENREF_RT595_BOOTSTRAP_RECOVERY_TRANSFER_RETURNED);
        assert(seen.authenticated && seen.image_base==0x08101000u && seen.image_size==0x2000u);
    }
    {
        openref_rt595_slot_authenticator_t authenticator={0};
        authenticator.initialized=true;
        authenticator.reader=(openref_rt595_slot_reader_t){never_read,NULL};
        state_store.loaded=true;
        state_store.state=(openref_boot_state_t){1u,1u,OPENREF_BOOT_SLOT_A,OPENREF_BOOT_NO_SLOT,0u};
        coordinator.authenticator=&authenticator;
        coordinator.maximum_trial_attempts=2u;
        assert(!openref_rt595_bootstrap_run(&bootstrap));
        assert(reason==OPENREF_RT595_BOOTSTRAP_RECOVERY_FLASH_READ);
        assert(authenticator.read_failures==2u && prepared==1u && transferred==1u);
    }
    bootstrap.recovery=NULL;
    coordinator.state_store=NULL;
    assert(!openref_rt595_bootstrap_run(&bootstrap));
    assert(recovered==3u);
    assert(reason==OPENREF_RT595_BOOTSTRAP_RECOVERY_CONFIGURATION);
    return 0;
}
