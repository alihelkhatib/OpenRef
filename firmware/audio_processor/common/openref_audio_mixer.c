#include "openref_audio_mixer.h"

#include <stddef.h>
#include <string.h>

#define OPENREF_AUDIO_DEFAULT_SOURCE_GAIN_Q15 16384u
#define OPENREF_AUDIO_LIMIT_RELEASE_SHIFT 4u

static int32_t absolute_i32(int32_t value)
{
    return value < 0 ? -value : value;
}

static int16_t saturate_i16(int32_t value, uint32_t *clipped_samples)
{
    if (value > INT16_MAX) {
        (*clipped_samples)++;
        return INT16_MAX;
    }
    if (value < INT16_MIN) {
        (*clipped_samples)++;
        return INT16_MIN;
    }
    return (int16_t)value;
}

void openref_audio_mixer_init(openref_audio_mixer_t *mixer)
{
    if (mixer == NULL) {
        return;
    }
    memset(mixer, 0, sizeof(*mixer));
    for (uint8_t index = 0u; index < OPENREF_AUDIO_REMOTE_SOURCES; index++) {
        mixer->source_gain_q15[index] = OPENREF_AUDIO_DEFAULT_SOURCE_GAIN_Q15;
    }
    mixer->limiter_gain_q15 = OPENREF_AUDIO_Q15_UNITY;
}

bool openref_audio_mixer_set_source_gain(
    openref_audio_mixer_t *mixer,
    uint8_t source_index,
    uint16_t gain_q15)
{
    if (mixer == NULL || source_index >= OPENREF_AUDIO_REMOTE_SOURCES ||
        gain_q15 > OPENREF_AUDIO_Q15_UNITY) {
        return false;
    }
    mixer->source_gain_q15[source_index] = gain_q15;
    return true;
}

void openref_audio_mixer_process(
    openref_audio_mixer_t *mixer,
    const int16_t sources[OPENREF_AUDIO_REMOTE_SOURCES][OPENREF_AUDIO_FRAME_SAMPLES],
    uint8_t valid_source_mask,
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES])
{
    if (mixer == NULL || sources == NULL || output == NULL) {
        return;
    }

    int32_t accumulation[OPENREF_AUDIO_FRAME_SAMPLES];
    memset(accumulation, 0, sizeof(accumulation));
    uint8_t active_sources = 0u;
    for (uint8_t source = 0u; source < OPENREF_AUDIO_REMOTE_SOURCES; source++) {
        if ((valid_source_mask & (1u << source)) == 0u) {
            continue;
        }
        active_sources++;
        int32_t gain = mixer->source_gain_q15[source];
        for (uint16_t sample = 0u; sample < OPENREF_AUDIO_FRAME_SAMPLES; sample++) {
            accumulation[sample] +=
                ((int32_t)sources[source][sample] * gain) >> 15;
        }
    }

    mixer->blocks++;
    if (active_sources == 0u) {
        memset(output, 0, OPENREF_AUDIO_FRAME_SAMPLES * sizeof(output[0]));
        mixer->silent_blocks++;
        mixer->last_prelimit_peak = 0;
        return;
    }

    int32_t peak = 0;
    for (uint16_t sample = 0u; sample < OPENREF_AUDIO_FRAME_SAMPLES; sample++) {
        int32_t magnitude = absolute_i32(accumulation[sample]);
        if (magnitude > peak) {
            peak = magnitude;
        }
    }
    mixer->last_prelimit_peak = peak;

    uint16_t requested_gain = OPENREF_AUDIO_Q15_UNITY;
    if (peak > (int32_t)OPENREF_AUDIO_LIMIT_TARGET) {
        requested_gain = (uint16_t)(((int64_t)OPENREF_AUDIO_LIMIT_TARGET << 15) / peak);
        mixer->limited_blocks++;
    }
    if (requested_gain < mixer->limiter_gain_q15) {
        mixer->limiter_gain_q15 = requested_gain;
    } else {
        uint32_t release = (OPENREF_AUDIO_Q15_UNITY - mixer->limiter_gain_q15) >>
                           OPENREF_AUDIO_LIMIT_RELEASE_SHIFT;
        mixer->limiter_gain_q15 = (uint16_t)(mixer->limiter_gain_q15 + release);
    }

    for (uint16_t sample = 0u; sample < OPENREF_AUDIO_FRAME_SAMPLES; sample++) {
        int32_t limited = (int32_t)(((int64_t)accumulation[sample] *
                                    mixer->limiter_gain_q15) >> 15);
        output[sample] = saturate_i16(limited, &mixer->clipped_samples);
    }
}
