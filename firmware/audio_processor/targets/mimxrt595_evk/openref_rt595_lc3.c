#include "openref_rt595_lc3.h"

#include <stddef.h>
#include <string.h>

#define OPENREF_RT595_LC3_SAMPLE_RATE_HZ 16000
#define OPENREF_RT595_LC3_FRAME_DURATION_US 10000
#define OPENREF_RT595_LC3_SAMPLE_BITS 16

bool openref_rt595_lc3_init(openref_rt595_lc3_t *codec)
{
    if (codec == NULL) {
        return false;
    }
    memset(codec, 0, sizeof(*codec));
    if (lc3_encoder_init(
            &codec->encoder, OPENREF_RT595_LC3_SAMPLE_RATE_HZ,
            OPENREF_RT595_LC3_FRAME_DURATION_US,
            OPENREF_AUDIO_CODEC_FRAME_BYTES,
            OPENREF_RT595_LC3_SAMPLE_BITS) != 0) {
        return false;
    }
    for (uint8_t index = 0u; index < OPENREF_AUDIO_REMOTE_SOURCES; index++) {
        if (lc3_decoder_init(
                &codec->decoders[index], OPENREF_RT595_LC3_SAMPLE_RATE_HZ,
                OPENREF_RT595_LC3_FRAME_DURATION_US,
                OPENREF_AUDIO_CODEC_FRAME_BYTES,
                OPENREF_RT595_LC3_SAMPLE_BITS) != 0) {
            return false;
        }
    }
    codec->initialized = true;
    return true;
}

bool openref_rt595_lc3_encode(
    void *context,
    const int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES])
{
    openref_rt595_lc3_t *codec = context;
    return codec != NULL && codec->initialized && pcm != NULL &&
        codec_frame != NULL &&
        lc3_encoder(&codec->encoder, (void *)pcm, codec_frame) == 0;
}

bool openref_rt595_lc3_decode(
    void *context,
    uint8_t decoder_index,
    const uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES],
    bool use_plc,
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES])
{
    openref_rt595_lc3_t *codec = context;
    if (codec == NULL || !codec->initialized ||
        decoder_index >= OPENREF_AUDIO_REMOTE_SOURCES || pcm == NULL ||
        codec_frame == NULL) {
        return false;
    }
    /* NXP's lc3_codec wrapper copies enc_bytes from input before applying the
     * bad-frame flag, so PLC still requires an addressable input buffer. The
     * portable playout boundary supplies a zero-filled frame for this case. */
    uint8_t *input = (uint8_t *)codec_frame;
    int frame_flag = use_plc ? LC3_FRAME_FLAG_BAD : LC3_FRAME_FLAG_GOOD;
    return lc3_decoder(
        &codec->decoders[decoder_index], input, frame_flag, pcm) == 0;
}
