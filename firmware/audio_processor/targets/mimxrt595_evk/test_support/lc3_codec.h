#ifndef LC3_CODEC_H
#define LC3_CODEC_H

#include <stdint.h>

#define LC3_FRAME_FLAG_GOOD 0
#define LC3_FRAME_FLAG_BAD 1

typedef struct {
    uint32_t instance;
} lc3_encoder_t;

typedef struct {
    uint32_t instance;
} lc3_decoder_t;

int lc3_encoder_init(lc3_encoder_t *encoder, int sample_rate, int duration_us,
    int target_bytes, int sample_bits);
int lc3_encoder(lc3_encoder_t *encoder, void *input, uint8_t *output);
int lc3_decoder_init(lc3_decoder_t *decoder, int sample_rate, int duration_us,
    int input_bytes, int sample_bits);
int lc3_decoder(lc3_decoder_t *decoder, uint8_t *input, int frame_flag,
    void *output);

#endif
