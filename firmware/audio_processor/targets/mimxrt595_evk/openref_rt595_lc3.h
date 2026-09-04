#ifndef OPENREF_RT595_LC3_H
#define OPENREF_RT595_LC3_H

#include <stdbool.h>
#include <stdint.h>

#include "lc3_codec.h"
#include "openref_audio_benchmark.h"

typedef struct {
    lc3_encoder_t encoder;
    lc3_decoder_t decoders[OPENREF_AUDIO_REMOTE_SOURCES];
    bool initialized;
} openref_rt595_lc3_t;

bool openref_rt595_lc3_init(openref_rt595_lc3_t *codec);

bool openref_rt595_lc3_encode(
    void *context,
    const int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES]);

bool openref_rt595_lc3_decode(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES]);

#endif
