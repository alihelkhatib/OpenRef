#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "openref_audio_playout.h"

static openref_audio_link_frame_t make_frame(uint8_t source, uint16_t sequence)
{
    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_REMOTE_AUDIO,
        .source_id = source,
        .flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                 OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID,
        .sequence = sequence,
    };
    for (uint8_t index = 0u; index < OPENREF_AUDIO_LINK_PAYLOAD_BYTES; index++) {
        frame.payload[index] = (uint8_t)(sequence + index);
    }
    return frame;
}

static void test_halves_and_gap_plc(void)
{
    openref_audio_playout_t playout;
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES];
    bool plc = true;
    openref_audio_playout_init(&playout);
    openref_audio_link_frame_t first = make_frame(2u, 10u);
    openref_audio_link_frame_t after_gap = make_frame(2u, 12u);
    assert(openref_audio_playout_push(&playout, &first));
    assert(openref_audio_playout_push(&playout, &after_gap));
    assert(openref_audio_playout_next(&playout, 2u, codec_frame, &plc) && !plc);
    assert(codec_frame[0] == 10u);
    assert(openref_audio_playout_next(&playout, 2u, codec_frame, &plc) && !plc);
    assert(codec_frame[0] == 50u);
    assert(openref_audio_playout_next(&playout, 2u, codec_frame, &plc) && plc);
    assert(openref_audio_playout_next(&playout, 2u, codec_frame, &plc) && plc);
    assert(openref_audio_playout_next(&playout, 2u, codec_frame, &plc) && !plc);
    assert(codec_frame[0] == 12u);
    assert(playout.sources[1].plc_frames == 2u);
}

static void test_duplicate_and_invalid_half(void)
{
    openref_audio_playout_t playout;
    uint8_t codec_frame[OPENREF_AUDIO_CODEC_FRAME_BYTES];
    bool plc = false;
    openref_audio_playout_init(&playout);
    openref_audio_link_frame_t frame = make_frame(1u, 20u);
    frame.flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID;
    assert(openref_audio_playout_push(&playout, &frame));
    assert(!openref_audio_playout_push(&playout, &frame));
    assert(playout.sources[0].duplicates == 1u);
    assert(openref_audio_playout_next(&playout, 1u, codec_frame, &plc) && !plc);
    assert(openref_audio_playout_next(&playout, 1u, codec_frame, &plc) && plc);
}

int main(void)
{
    test_halves_and_gap_plc();
    test_duplicate_and_invalid_half();
    return 0;
}
