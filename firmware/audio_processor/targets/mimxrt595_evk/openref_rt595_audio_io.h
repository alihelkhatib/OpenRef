#ifndef OPENREF_RT595_AUDIO_IO_H
#define OPENREF_RT595_AUDIO_IO_H
#include <stdbool.h>
#include <stdint.h>
#define OPENREF_RT595_AUDIO_IO_SAMPLE_RATE_HZ 16000u
#define OPENREF_RT595_AUDIO_IO_BLOCK_SAMPLES 160u
typedef bool (*openref_rt595_audio_io_start_fn)(void *, int16_t *, uint16_t);
typedef void (*openref_rt595_audio_io_abort_fn)(void *);
typedef void (*openref_rt595_audio_io_critical_fn)(void *);
typedef struct {openref_rt595_audio_io_start_fn capture;openref_rt595_audio_io_start_fn playout;openref_rt595_audio_io_abort_fn abort;openref_rt595_audio_io_critical_fn enter_critical,exit_critical;void *context;} openref_rt595_audio_io_ops_t;
typedef struct {
 openref_rt595_audio_io_ops_t ops; int16_t capture[2][OPENREF_RT595_AUDIO_IO_BLOCK_SAMPLES]; int16_t playout[2][OPENREF_RT595_AUDIO_IO_BLOCK_SAMPLES];
 volatile bool capture_ready[2]; volatile bool capture_active,playout_active; bool playout_ready[2]; uint8_t capture_index,playout_index;
 uint32_t capture_blocks,playout_blocks,capture_overruns,playout_underruns,dma_failures; bool initialized;
} openref_rt595_audio_io_t;
bool openref_rt595_audio_io_init(openref_rt595_audio_io_t *,const openref_rt595_audio_io_ops_t *);
void openref_rt595_audio_io_capture_complete(openref_rt595_audio_io_t *,bool success);
void openref_rt595_audio_io_playout_complete(openref_rt595_audio_io_t *,bool success);
bool openref_rt595_audio_io_take_capture(openref_rt595_audio_io_t *,int16_t out[OPENREF_RT595_AUDIO_IO_BLOCK_SAMPLES]);
bool openref_rt595_audio_io_submit_playout(openref_rt595_audio_io_t *,const int16_t in[OPENREF_RT595_AUDIO_IO_BLOCK_SAMPLES]);
void openref_rt595_audio_io_stop(openref_rt595_audio_io_t *);
#endif
