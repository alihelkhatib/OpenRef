#ifndef OPENREF_RT595_OUTPUT_GUARD_H
#define OPENREF_RT595_OUTPUT_GUARD_H
#include <stdbool.h>
#include <stdint.h>
typedef bool (*openref_rt595_output_mute_fn)(void *, bool);
typedef void (*openref_rt595_output_shutdown_fn)(void *);
typedef struct {openref_rt595_output_mute_fn set_muted;openref_rt595_output_shutdown_fn stop_audio,abort_link;void *context;} openref_rt595_output_guard_ops_t;
typedef struct {openref_rt595_output_guard_ops_t ops;uint32_t faults;bool initialized,muted,enabled,fault_latched;} openref_rt595_output_guard_t;
bool openref_rt595_output_guard_init(openref_rt595_output_guard_t *,const openref_rt595_output_guard_ops_t *);
bool openref_rt595_output_guard_set_ready(openref_rt595_output_guard_t *,bool runtime_ready,bool peer_ready,bool watchdog_ready);
void openref_rt595_output_guard_fault(openref_rt595_output_guard_t *);
#endif
