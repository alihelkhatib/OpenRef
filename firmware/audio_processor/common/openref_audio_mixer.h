#ifndef OPENREF_AUDIO_MIXER_H
#define OPENREF_AUDIO_MIXER_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_AUDIO_SAMPLE_RATE_HZ 16000u
#define OPENREF_AUDIO_FRAME_SAMPLES 160u
#define OPENREF_AUDIO_REMOTE_SOURCES 5u
#define OPENREF_AUDIO_Q15_UNITY 32768u
#define OPENREF_AUDIO_LIMIT_TARGET 30000u

typedef struct {
    uint16_t source_gain_q15[OPENREF_AUDIO_REMOTE_SOURCES];
    uint16_t limiter_gain_q15;
    uint32_t blocks;
    uint32_t silent_blocks;
    uint32_t limited_blocks;
    uint32_t clipped_samples;
    int32_t last_prelimit_peak;
} openref_audio_mixer_t;

void openref_audio_mixer_init(openref_audio_mixer_t *mixer);

bool openref_audio_mixer_set_source_gain(
    openref_audio_mixer_t *mixer,
    uint8_t source_index,
    uint16_t gain_q15);

void openref_audio_mixer_process(
    openref_audio_mixer_t *mixer,
    const int16_t sources[OPENREF_AUDIO_REMOTE_SOURCES][OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t valid_source_mask,
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES]);

#ifdef __cplusplus
}
#endif

#endif
