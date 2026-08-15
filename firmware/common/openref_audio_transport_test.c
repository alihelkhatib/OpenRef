#include <assert.h>
#include <string.h>

#include "openref_audio_transport.h"

static openref_audio_link_frame_t audio_frame(uint16_t sequence)
{
    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_REMOTE_AUDIO,
        .source_id = 2u,
        .flags = OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID |
                 OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID,
        .sequence = sequence,
    };
    memset(frame.payload, (int)(sequence & 0xffu), sizeof(frame.payload));
    return frame;
}

static openref_audio_link_frame_t status_frame(uint16_t sequence)
{
    openref_audio_link_frame_t frame = {
        .kind = OPENREF_AUDIO_LINK_STATUS,
        .source_id = 0u,
        .sequence = sequence,
    };
    return frame;
}

static void test_audio_priority_and_request(void)
{
    openref_audio_transport_t transport;
    openref_audio_transport_init(&transport);
    openref_audio_link_frame_t status = status_frame(7u);
    openref_audio_link_frame_t audio = audio_frame(9u);
    assert(openref_audio_transport_queue(&transport, &status));
    assert(openref_audio_transport_queue(&transport, &audio));
    assert(openref_audio_transport_request_asserted(&transport));

    uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    openref_audio_link_frame_t decoded;
    assert(openref_audio_transport_prepare_tx(&transport, 100u, wire));
    assert(openref_audio_link_decode(wire, sizeof(wire), &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_REMOTE_AUDIO);
    assert(decoded.sequence == 9u);
    assert(openref_audio_transport_request_asserted(&transport));
    assert(openref_audio_transport_prepare_tx(&transport, 200u, wire));
    assert(openref_audio_link_decode(wire, sizeof(wire), &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_STATUS);
    assert(decoded.sequence == 7u);
    assert(!openref_audio_transport_request_asserted(&transport));
}

static void test_idle_and_receive_diagnostics(void)
{
    openref_audio_transport_t transport;
    openref_audio_transport_init(&transport);
    uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    openref_audio_link_frame_t decoded;
    assert(openref_audio_transport_prepare_tx(&transport, 1234u, wire));
    assert(openref_audio_link_decode(wire, sizeof(wire), &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_STATUS);
    assert(decoded.timestamp_us == 1234u);
    assert(transport.idle_transactions == 1u);

    openref_audio_link_frame_t first = audio_frame(10u);
    assert(openref_audio_link_encode(&first, wire, sizeof(wire)));
    assert(openref_audio_transport_accept_rx(&transport, wire));
    openref_audio_link_frame_t gap = audio_frame(12u);
    assert(openref_audio_link_encode(&gap, wire, sizeof(wire)));
    assert(openref_audio_transport_accept_rx(&transport, wire));
    assert(transport.sequence_gaps == 1u);
    assert(openref_audio_transport_pop_audio(&transport, &decoded));
    assert(decoded.sequence == 10u);
    assert(openref_audio_transport_pop_audio(&transport, &decoded));
    assert((decoded.flags & OPENREF_AUDIO_LINK_FLAG_DISCONTINUITY) != 0u);

    wire[20] ^= 1u;
    assert(!openref_audio_transport_accept_rx(&transport, wire));
    assert(transport.malformed_frames == 1u);
}

static void test_latest_status_replaces_old_status(void)
{
    openref_audio_transport_t transport;
    openref_audio_transport_init(&transport);
    openref_audio_link_frame_t old_status = status_frame(1u);
    openref_audio_link_frame_t new_status = status_frame(2u);
    assert(openref_audio_transport_queue(&transport, &old_status));
    assert(openref_audio_transport_queue(&transport, &new_status));
    uint8_t wire[OPENREF_AUDIO_LINK_FRAME_BYTES];
    openref_audio_link_frame_t decoded;
    assert(openref_audio_transport_prepare_tx(&transport, 0u, wire));
    assert(openref_audio_link_decode(wire, sizeof(wire), &decoded));
    assert(decoded.sequence == 2u);
}

int main(void)
{
    test_audio_priority_and_request();
    test_idle_and_receive_diagnostics();
    test_latest_status_replaces_old_status();
    return 0;
}
