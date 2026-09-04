#include "openref_rt595_audio_spi.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    const uint8_t *tx;
    uint8_t *rx;
    uint16_t bytes;
    unsigned starts;
    unsigned aborts;
    bool request;
    bool start_ok;
} fake_t;

static bool fake_start(void *context, const uint8_t *tx, uint8_t *rx, uint16_t bytes)
{
    fake_t *fake = context;
    fake->tx = tx;
    fake->rx = rx;
    fake->bytes = bytes;
    ++fake->starts;
    return fake->start_ok;
}

static void fake_abort(void *context) { ++((fake_t *)context)->aborts; }
static void fake_request(void *context, bool asserted) { ((fake_t *)context)->request = asserted; }

static openref_audio_link_frame_t frame(uint8_t kind, uint8_t source, uint16_t sequence)
{
    openref_audio_link_frame_t result = {0};
    result.kind = kind;
    result.source_id = source;
    result.sequence = sequence;
    result.payload[0] = (uint8_t)sequence;
    return result;
}

static openref_rt595_audio_spi_t setup(fake_t *fake)
{
    openref_rt595_audio_spi_t spi;
    openref_rt595_audio_spi_ops_t ops = {fake_start, fake_abort, fake_request, fake};
    fake->start_ok = true;
    assert(openref_rt595_audio_spi_init(&spi, &ops));
    return spi;
}

static void test_idle_and_queued_transaction(void)
{
    fake_t fake = {0};
    openref_rt595_audio_spi_t spi = setup(&fake);
    openref_audio_link_frame_t decoded;
    openref_audio_link_frame_t queued = frame(OPENREF_AUDIO_LINK_LOCAL_AUDIO, 1, 7);
    openref_audio_link_frame_t incoming = frame(OPENREF_AUDIO_LINK_REMOTE_AUDIO, 2, 9);

    openref_rt595_audio_spi_poll(&spi, 100);
    assert(fake.starts == 1 && fake.bytes == OPENREF_AUDIO_LINK_FRAME_BYTES && !fake.request);
    assert(openref_audio_link_decode(fake.tx, OPENREF_AUDIO_LINK_FRAME_BYTES, &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_STATUS);
    assert(openref_rt595_audio_spi_queue(&spi, &queued));
    assert(fake.request);
    assert(openref_audio_link_encode(&incoming, fake.rx, OPENREF_AUDIO_LINK_FRAME_BYTES));
    openref_rt595_audio_spi_complete(&spi, true, OPENREF_AUDIO_LINK_FRAME_BYTES);
    openref_rt595_audio_spi_poll(&spi, 200);
    assert(fake.starts == 2 && fake.request);
    assert(openref_audio_link_decode(fake.tx, OPENREF_AUDIO_LINK_FRAME_BYTES, &decoded));
    assert(decoded.kind == OPENREF_AUDIO_LINK_LOCAL_AUDIO && decoded.sequence == 7);
    assert(openref_rt595_audio_spi_pop_audio(&spi, &decoded));
    assert(decoded.source_id == 2 && decoded.sequence == 9);
    openref_rt595_audio_spi_complete(&spi, true, OPENREF_AUDIO_LINK_FRAME_BYTES);
    openref_rt595_audio_spi_poll(&spi, 300);
    assert(!fake.request);
}

static void test_bad_completion_is_fail_closed(void)
{
    fake_t fake = {0};
    openref_rt595_audio_spi_t spi = setup(&fake);
    openref_audio_link_frame_t decoded;
    openref_rt595_audio_spi_poll(&spi, 0);
    memset(fake.rx, 0x55, OPENREF_AUDIO_LINK_FRAME_BYTES);
    openref_rt595_audio_spi_complete(&spi, true, OPENREF_AUDIO_LINK_FRAME_BYTES - 1);
    openref_rt595_audio_spi_poll(&spi, 1);
    assert(spi.short_transfers == 1);
    assert(!openref_rt595_audio_spi_pop_audio(&spi, &decoded));
    memset(fake.rx, 0, OPENREF_AUDIO_LINK_FRAME_BYTES);
    openref_rt595_audio_spi_complete(&spi, true, OPENREF_AUDIO_LINK_FRAME_BYTES);
    openref_rt595_audio_spi_poll(&spi, 2);
    assert(spi.transport.malformed_frames == 1);
    assert(!openref_rt595_audio_spi_pop_audio(&spi, &decoded));
}

static void test_start_failure_and_reset(void)
{
    fake_t fake = {0};
    openref_rt595_audio_spi_t spi = setup(&fake);
    openref_audio_link_frame_t queued = frame(OPENREF_AUDIO_LINK_LOCAL_AUDIO, 1, 2);
    fake.start_ok = false;
    assert(openref_rt595_audio_spi_queue(&spi, &queued));
    openref_rt595_audio_spi_poll(&spi, 0);
    assert(spi.start_failures == 1 && !spi.transfer_active && !fake.request);
    fake.start_ok = true;
    openref_rt595_audio_spi_poll(&spi, 1);
    assert(spi.transfer_active);
    openref_rt595_audio_spi_reset(&spi);
    assert(fake.aborts == 1 && !fake.request && spi.resets == 1);
}

int main(void)
{
    test_idle_and_queued_transaction();
    test_bad_completion_is_fail_closed();
    test_start_failure_and_reset();
    puts("openref_rt595_audio_spi_test: PASS");
    return 0;
}
