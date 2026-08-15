#include <assert.h>
#include <stdint.h>

#include "openref_diagnostics.h"

int main(void)
{
    openref_diagnostics_t diagnostics;
    openref_diagnostics_init(&diagnostics);
    assert(!openref_diagnostics_record(
        &diagnostics, 0u, (openref_diagnostic_event_code_t)0,
        OPENREF_DIAGNOSTIC_INFO, 0u, 0u));
    for (uint32_t index = 0u; index < 40u; index++) {
        assert(openref_diagnostics_record(
            &diagnostics, index, OPENREF_EVENT_AUDIO_DEADLINE_MISS,
            OPENREF_DIAGNOSTIC_ERROR, 2u, index + 100u));
    }
    assert(diagnostics.count == OPENREF_DIAGNOSTIC_CAPACITY);
    assert(diagnostics.recorded == 40u);
    assert(diagnostics.overwritten == 8u);

    openref_diagnostic_event_t event;
    assert(openref_diagnostics_peek(&diagnostics, 0u, &event));
    assert(event.timestamp_ms == 8u);
    assert(event.value == 108u);
    assert(openref_diagnostics_peek(&diagnostics, 31u, &event));
    assert(event.timestamp_ms == 39u);
    for (uint8_t index = 8u; index < 40u; index++) {
        assert(openref_diagnostics_pop(&diagnostics, &event));
        assert(event.timestamp_ms == index);
    }
    assert(!openref_diagnostics_pop(&diagnostics, &event));

    const openref_diagnostic_event_t vector = {
        .timestamp_ms = UINT64_C(0x0102030405060708),
        .value = 0x11121314u,
        .code = OPENREF_EVENT_PEER_POWER_CYCLE,
        .source_id = 6u,
        .severity = OPENREF_DIAGNOSTIC_FATAL,
    };
    uint8_t wire[OPENREF_DIAGNOSTIC_WIRE_BYTES];
    assert(openref_diagnostic_encode(&vector, wire));
    const uint8_t expected[OPENREF_DIAGNOSTIC_WIRE_BYTES] = {
        0x08u, 0x07u, 0x06u, 0x05u, 0x04u, 0x03u, 0x02u, 0x01u,
        0x14u, 0x13u, 0x12u, 0x11u, 0x31u, 0x00u, 0x06u, 0x03u,
    };
    for (uint8_t index = 0u; index < sizeof(expected); index++) {
        assert(wire[index] == expected[index]);
    }
    assert(openref_diagnostic_decode(wire, &event));
    assert(event.timestamp_ms == vector.timestamp_ms);
    assert(event.value == vector.value);
    assert(event.code == vector.code);
    return 0;
}
