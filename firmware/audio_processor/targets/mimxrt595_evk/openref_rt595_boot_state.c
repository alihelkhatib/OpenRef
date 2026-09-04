#include "openref_rt595_boot_state.h"
#include <stddef.h>
#include <string.h>

static void put32(uint8_t *p,uint32_t v){for(uint8_t i=0;i<4u;i++)p[i]=(uint8_t)(v>>(8u*i));}
static uint32_t get32(const uint8_t*p){uint32_t v=0;for(uint8_t i=0;i<4u;i++)v|=(uint32_t)p[i]<<(8u*i);return v;}
static void encode(const openref_boot_state_t*s,uint8_t*p){memset(p,0,OPENREF_CONFIG_MAX_PAYLOAD_BYTES);put32(p,s->record_version);put32(p+4,s->minimum_version);p[8]=s->confirmed_slot;p[9]=s->pending_slot;p[10]=s->pending_attempts;}
static void decode(openref_boot_state_t*s,const uint8_t*p){*s=(openref_boot_state_t){get32(p),get32(p+4),p[8],p[9],p[10]};}
static bool save(openref_rt595_boot_state_store_t*b){uint8_t p[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];encode(&b->state,p);return openref_config_store_save(&b->store,p);}

bool openref_rt595_boot_state_init(openref_rt595_boot_state_store_t*b,openref_config_backend_t backend){if(!b)return false;memset(b,0,sizeof(*b));return openref_config_store_init(&b->store,backend,OPENREF_RT595_BOOT_STATE_SCHEMA,OPENREF_RT595_BOOT_STATE_PAYLOAD_BYTES);}
bool openref_rt595_boot_state_load(openref_rt595_boot_state_store_t*b){uint8_t p[OPENREF_CONFIG_MAX_PAYLOAD_BYTES];if(!b||!openref_config_store_load(&b->store,p))return false;decode(&b->state,p);b->loaded=openref_boot_policy_state_valid(&b->state);return b->loaded;}
bool openref_rt595_boot_state_initialize(openref_rt595_boot_state_store_t*b,uint8_t confirmed,uint32_t minimum){if(!b||b->loaded||(confirmed!=OPENREF_BOOT_SLOT_A&&confirmed!=OPENREF_BOOT_SLOT_B))return false;b->state=(openref_boot_state_t){1u,minimum,confirmed,OPENREF_BOOT_NO_SLOT,0u};if(!save(b)){memset(&b->state,0,sizeof(b->state));return false;}b->loaded=true;return true;}
bool openref_rt595_boot_state_stage(openref_rt595_boot_state_store_t*b,uint8_t candidate,const openref_boot_slot_t slots[2]){if(!b||!b->loaded)return false;openref_boot_state_t old=b->state;if(!openref_boot_policy_stage(&b->state,candidate,slots)||!save(b)){b->state=old;return false;}return true;}
openref_boot_decision_t openref_rt595_boot_state_select(openref_rt595_boot_state_store_t*b,const openref_boot_slot_t slots[2],uint8_t maximum){openref_boot_decision_t none={OPENREF_BOOT_NO_SLOT,OPENREF_BOOT_DECISION_NONE,false};if(!b||!b->loaded)return none;openref_boot_state_t old=b->state;openref_boot_decision_t d=openref_boot_policy_select(&b->state,slots,maximum);if(d.state_changed&&!save(b)){b->state=old;return none;}return d;}
bool openref_rt595_boot_state_confirm(openref_rt595_boot_state_store_t*b,uint8_t running,const openref_boot_slot_t slots[2]){if(!b||!b->loaded)return false;openref_boot_state_t old=b->state;if(!openref_boot_policy_confirm(&b->state,running,slots)||!save(b)){b->state=old;return false;}return true;}
