#include "openref_rt595_lc3.h"

#include <assert.h>
#include <stddef.h>
#include <string.h>

static lc3_decoder_t *initialized_decoders[OPENREF_AUDIO_REMOTE_SOURCES];
static uint8_t decoder_init_count;
static uint8_t *last_decoder_input;
static int last_frame_flag;

int lc3_encoder_init(lc3_encoder_t *encoder, int sample_rate, int duration_us,
    int target_bytes, int sample_bits)
{
    assert(sample_rate == 16000 && duration_us == 10000);
    assert(target_bytes == 40 && sample_bits == 16);
    encoder->instance = 1u;
    return 0;
}

int lc3_decoder_init(lc3_decoder_t *decoder, int sample_rate, int duration_us,
    int input_bytes, int sample_bits)
{
    assert(sample_rate == 16000 && duration_us == 10000);
    assert(input_bytes == 40 && sample_bits == 16);
    assert(decoder_init_count < OPENREF_AUDIO_REMOTE_SOURCES);
    initialized_decoders[decoder_init_count] = decoder;
    decoder->instance = (uint32_t)decoder_init_count + 1u;
    decoder_init_count++;
    return 0;
}

int lc3_encoder(lc3_encoder_t *encoder, void *input, uint8_t *output)
{
    assert(encoder != NULL && input != NULL && output != NULL);
    memset(output, 0x5a, OPENREF_AUDIO_CODEC_FRAME_BYTES);
    return 0;
}

int lc3_decoder(lc3_decoder_t *decoder, uint8_t *input, int frame_flag,
    void *output)
{
    assert(decoder != NULL && output != NULL);
    last_decoder_input = input;
    last_frame_flag = frame_flag;
    memset(output, 0, OPENREF_AUDIO_FRAME_SAMPLES * sizeof(int16_t));
    return 0;
}

static void test_initializes_one_encoder_and_five_distinct_decoders(void)
{
    openref_rt595_lc3_t codec;
    assert(openref_rt595_lc3_init(&codec));
    assert(codec.initialized && codec.encoder.instance == 1u);
    assert(decoder_init_count == OPENREF_AUDIO_REMOTE_SOURCES);
    for (uint8_t index = 0u; index < decoder_init_count; index++) {
        assert(initialized_decoders[index] == &codec.decoders[index]);
        for (uint8_t other = 0u; other < index; other++) {
            assert(initialized_decoders[index] != initialized_decoders[other]);
        }
    }
}

static void test_plc_passes_addressable_frame_with_bad_flag(void)
{
    openref_rt595_lc3_t codec;
    decoder_init_count = 0u;
    assert(openref_rt595_lc3_init(&codec));
    uint8_t frame[OPENREF_AUDIO_CODEC_FRAME_BYTES] = {0u};
    int16_t pcm[OPENREF_AUDIO_FRAME_SAMPLES];
    assert(openref_rt595_lc3_decode(&codec, 3u, frame, true, pcm));
    assert(last_decoder_input == frame);
    assert(last_frame_flag == LC3_FRAME_FLAG_BAD);
    assert(openref_rt595_lc3_decode(&codec, 3u, frame, false, pcm));
    assert(last_decoder_input == frame);
    assert(last_frame_flag == LC3_FRAME_FLAG_GOOD);
    assert(!openref_rt595_lc3_decode(
        &codec, OPENREF_AUDIO_REMOTE_SOURCES, frame, false, pcm));
}

int main(void)
{
    test_initializes_one_encoder_and_five_distinct_decoders();
    test_plc_passes_addressable_frame_with_bad_flag();
    return 0;
}
