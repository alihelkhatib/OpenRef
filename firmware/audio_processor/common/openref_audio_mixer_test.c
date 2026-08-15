#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "openref_audio_mixer.h"

static void test_silence(void)
{
    openref_audio_mixer_t mixer;
    int16_t sources[OPENREF_AUDIO_REMOTE_SOURCES][OPENREF_AUDIO_FRAME_SAMPLES] = {{0}};
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES];
    memset(output, 0x55, sizeof(output));
    openref_audio_mixer_init(&mixer);
    openref_audio_mixer_process(&mixer, sources, 0u, output);
    for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
        assert(output[index] == 0);
    }
    assert(mixer.silent_blocks == 1u);
}

static void test_single_source_gain(void)
{
    openref_audio_mixer_t mixer;
    int16_t sources[OPENREF_AUDIO_REMOTE_SOURCES][OPENREF_AUDIO_FRAME_SAMPLES] = {{0}};
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES];
    for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
        sources[0][index] = 12000;
    }
    openref_audio_mixer_init(&mixer);
    assert(openref_audio_mixer_set_source_gain(&mixer, 0u, OPENREF_AUDIO_Q15_UNITY));
    assert(!openref_audio_mixer_set_source_gain(&mixer, OPENREF_AUDIO_REMOTE_SOURCES, 1u));
    openref_audio_mixer_process(&mixer, sources, 1u, output);
    assert(output[0] == 12000);
    assert(mixer.limited_blocks == 0u);
}

static void test_limiter(void)
{
    openref_audio_mixer_t mixer;
    int16_t sources[OPENREF_AUDIO_REMOTE_SOURCES][OPENREF_AUDIO_FRAME_SAMPLES];
    int16_t output[OPENREF_AUDIO_FRAME_SAMPLES];
    for (uint8_t source = 0u; source < OPENREF_AUDIO_REMOTE_SOURCES; source++) {
        for (uint16_t index = 0u; index < OPENREF_AUDIO_FRAME_SAMPLES; index++) {
            sources[source][index] = INT16_MAX;
        }
    }
    openref_audio_mixer_init(&mixer);
    openref_audio_mixer_process(&mixer, sources, 0x1fu, output);
    assert(mixer.limited_blocks == 1u);
    assert(mixer.last_prelimit_peak > (int32_t)OPENREF_AUDIO_LIMIT_TARGET);
    assert(output[0] <= (int16_t)OPENREF_AUDIO_LIMIT_TARGET);
    assert(mixer.clipped_samples == 0u);
}

int main(void)
{
    test_silence();
    test_single_source_gain();
    test_limiter();
    return 0;
}
