#include "openref_rt595_output_guard.h"
#include <limits.h>
#include <stddef.h>
#include <string.h>
void openref_rt595_output_guard_fault(openref_rt595_output_guard_t *g)
{
    if (!g || !g->initialized) return;
    if (g->faults != UINT32_MAX) ++g->faults;
    g->fault_latched = true;
    g->enabled = false;
    /* Mute before stopping DMA so a partially shifted buffer cannot be audible. */
    g->muted = g->ops.set_muted(g->ops.context, true);
    g->ops.stop_audio(g->ops.context);
    g->ops.abort_link(g->ops.context);
}
bool openref_rt595_output_guard_init(openref_rt595_output_guard_t *g,const openref_rt595_output_guard_ops_t *o)
{
    if (!g || !o || !o->set_muted || !o->stop_audio || !o->abort_link) return false;
    memset(g,0,sizeof(*g));g->ops=*o;g->initialized=true;
    if (!g->ops.set_muted(g->ops.context,true)) {openref_rt595_output_guard_fault(g);return false;}
    g->muted=true;return true;
}
bool openref_rt595_output_guard_set_ready(openref_rt595_output_guard_t *g,bool runtime_ready,bool peer_ready,bool watchdog_ready)
{
    if (!g || !g->initialized || g->fault_latched) return false;
    if (!(runtime_ready && peer_ready && watchdog_ready)) {
        if (g->enabled) { openref_rt595_output_guard_fault(g); return false; }
        return g->muted;
    }
    if (g->enabled) return true;
    if (!g->ops.set_muted(g->ops.context,false)) {openref_rt595_output_guard_fault(g);return false;}
    g->muted=false;g->enabled=true;return true;
}
