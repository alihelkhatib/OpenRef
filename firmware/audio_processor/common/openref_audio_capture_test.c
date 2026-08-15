#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "openref_audio_capture.h"

int main(void)
{
    openref_audio_capture_t capture;
    uint8_t first[OPENREF_AUDIO_CAPTURE_CODEC_BYTES];
    uint8_t second[OPENREF_AUDIO_CAPTURE_CODEC_BYTES];
    for (uint8_t index = 0u; index < OPENREF_AUDIO_CAPTURE_CODEC_BYTES; index++) {
        first[index] = index;
        second[index] = (uint8_t)(index + 40u);
    }
    assert(openref_audio_capture_init(&capture, 3u, 0xffffu));
    assert(openref_audio_capture_submit(&capture, first, true, false, 1000u));
    assert(capture.output_queue.count == 0u);
    assert(openref_audio_capture_submit(&capture, second, true, true, 11000u));
    assert(capture.output_queue.count == 1u);

    openref_audio_link_frame_t frame;
    assert(openref_audio_capture_pop(&capture, &frame));
    assert(frame.kind == OPENREF_AUDIO_LINK_LOCAL_AUDIO);
    assert(frame.source_id == 3u);
    assert(frame.sequence == 0xffffu);
    assert(frame.timestamp_us == 1000u);
    assert(frame.flags == (OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                           OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID |
                           OPENREF_AUDIO_LINK_FLAG_DISCONTINUITY));
    assert(frame.payload[0] == 0u && frame.payload[79] == 79u);
    assert(capture.next_sequence == 0u);

    assert(openref_audio_capture_submit(&capture, NULL, false, false, 21000u));
    assert(openref_audio_capture_submit(&capture, second, true, false, 31000u));
    assert(openref_audio_capture_pop(&capture, &frame));
    assert((frame.flags & OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID) == 0u);
    assert((frame.flags & OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID) != 0u);
    assert(capture.invalid_codec_frames == 1u);
    return 0;
}
