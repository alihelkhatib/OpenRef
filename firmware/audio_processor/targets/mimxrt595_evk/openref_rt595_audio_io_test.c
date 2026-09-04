#include "openref_rt595_audio_io.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct{int16_t*rx,*tx;unsigned rxs,txs,abort;}fake_t;
static bool rx(void*c,int16_t*b,uint16_t n){fake_t*f=c;assert(n==160);f->rx=b;f->rxs++;return true;}
static bool tx(void*c,int16_t*b,uint16_t n){fake_t*f=c;assert(n==160);f->tx=b;f->txs++;return true;}
static void ab(void*c){((fake_t*)c)->abort++;}
static void critical(void*c){(void)c;}
int main(void){fake_t f={0};openref_rt595_audio_io_t io;openref_rt595_audio_io_ops_t o={rx,tx,ab,critical,critical,&f};int16_t b[160];assert(openref_rt595_audio_io_init(&io,&o));for(unsigned i=0;i<160;i++)f.rx[i]=(int16_t)i;openref_rt595_audio_io_capture_complete(&io,true);assert(openref_rt595_audio_io_take_capture(&io,b)&&b[159]==159);memset(b,7,sizeof(b));assert(openref_rt595_audio_io_submit_playout(&io,b));openref_rt595_audio_io_playout_complete(&io,true);assert(f.tx[0]==1799);openref_rt595_audio_io_playout_complete(&io,true);assert(io.playout_underruns==1&&f.tx[0]==0);openref_rt595_audio_io_capture_complete(&io,true);openref_rt595_audio_io_capture_complete(&io,true);assert(io.capture_overruns==1);openref_rt595_audio_io_stop(&io);assert(f.abort==1);puts("openref_rt595_audio_io_test: PASS");return 0;}
