#include <assert.h>
#include <stdint.h>

#include "openref_audio_link.h"

static openref_audio_link_frame_t make_frame(uint16_t sequence)
{
    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_REMOTE_AUDIO,
        .source_id = 3u,
        .flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                 OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID,
        .sequence = sequence,
        .timestamp_us = 0x01020304u,
        .producer_queue_depth = 2u,
    };
    for (uint8_t index = 0u; index < OPENREF_AUDIO_LINK_PAYLOAD_BYTES; index++) {
        frame.payload[index] = index;
    }
    return frame;
}

static void test_wire_round_trip_and_crc(void)
{
    openref_audio_link_frame_t expected = make_frame(0x1234u);
    uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    assert(openref_audio_link_encode(&expected, wire, sizeof(wire)));
    assert(wire[0] == 0x4fu && wire[1] == 0x41u);
    assert(wire[96] == 0xaau && wire[97] == 0x0au);
    openref_audio_link_frame_t decoded;
    assert(openref_audio_link_decode(wire, sizeof(wire), &decoded));
    assert(decoded.sequence == expected.sequence);
    assert(decoded.payload[0] == 0u && decoded.payload[79] == 79u);
    wire[20] ^= 1u;
    assert(!openref_audio_link_decode(wire, sizeof(wire), &decoded));
}

static void test_queue_drops_oldest(void)
{
    openref_audio_link_queue_t queue;
    openref_audio_link_queue_init(&queue);
    for (uint16_t sequence = 0u; sequence < 5u; sequence++) {
        openref_audio_link_frame_t frame = make_frame(sequence);
        assert(openref_audio_link_queue_push(&queue, &frame));
    }
    assert(queue.count == OPENREF_AUDIO_LINK_QUEUE_CAPACITY);
    assert(queue.overruns == 1u);
    openref_audio_link_frame_t frame;
    assert(openref_audio_link_queue_pop(&queue, &frame));
    assert(frame.sequence == 1u);
}

int main(void)
{
    test_wire_round_trip_and_crc();
    test_queue_drops_oldest();
    return 0;
}
