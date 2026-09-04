#include "openref_rt595_output_guard.h"
#include <assert.h>
typedef struct {unsigned sequence;unsigned mute_order,stop_order,abort_order;bool mute_ok;} fake_t;
static bool mute(void*c,bool m){fake_t*f=c;(void)m;f->mute_order=++f->sequence;return f->mute_ok;}
static void stop(void*c){fake_t*f=c;f->stop_order=++f->sequence;}
static void abort_link(void*c){fake_t*f=c;f->abort_order=++f->sequence;}
int main(void){openref_rt595_output_guard_t g;fake_t f={.mute_ok=true};openref_rt595_output_guard_ops_t o={mute,stop,abort_link,&f};assert(openref_rt595_output_guard_init(&g,&o));assert(g.muted&&!g.enabled);assert(openref_rt595_output_guard_set_ready(&g,true,false,true));assert(g.muted);assert(openref_rt595_output_guard_set_ready(&g,true,true,true));assert(g.enabled&&!g.muted);assert(!openref_rt595_output_guard_set_ready(&g,true,true,false));assert(g.fault_latched&&g.muted&&!g.enabled);assert(f.mute_order<f.stop_order&&f.stop_order<f.abort_order);f=(fake_t){0};assert(openref_rt595_output_guard_init(&g,&o)==false);assert(g.fault_latched&&!g.muted);assert(f.mute_order<f.stop_order&&f.stop_order<f.abort_order);return 0;}
