# FG23 LC3 benchmark result (2026-08-14)

## Decision

Use the EFR32FG23 as the radio/network processor and a separate audio
processor for capture, LC3, mixing, and playback. Upstream `google/liblc3` is
functional on the FG23, but the measured six-participant codec workload cannot
meet its real-time deadline on this processor.

## Configuration

- EFR32FG23B010F512IM48 on BRD2600A
- Silicon Labs GCC 14.2.1, Cortex-M33 hard-float
- `google/liblc3` commit `ce2e41faf8c06d038df9f32504c61109a14130be`
- mono, 16 kHz, 10 ms, 40 bytes (32 kbit/s)
- one encoder followed by five independent decoders
- 8,192-byte main stack and concurrent OpenRef scheduled network node 1

## Footprint

| Image | text | data | bss |
|---|---:|---:|---:|
| Network baseline | 247,096 B | 2,004 B | 63,544 B |
| Network + LC3 benchmark | 328,144 B | 2,632 B | 62,916 B |
| Difference | +81,048 B | +628 B | -628 B |

The apparent BSS decrease occurs because the Silicon Labs linker fills unused
RAM with a managed heap. Codec-owned persistent allocations from the map are
2,600 bytes of encoder state, 15,720 bytes for five decoder states, 1,920 bytes
of PCM buffers, and a 40-byte encoded frame: 20,280 bytes total, excluding
pointers and stack.

The generated RAILtest project initially reserved a 2,048-byte stack and
stalled on its first encode. An 8,192-byte stack ran reliably. Exact stack
high-water must be measured again in product firmware.

## Timing

Across runs 5 through 19:

- encode: 6,616-6,623 us
- five decodes: 16,395-16,428 us
- encode plus five decodes: 23,017-23,051 us
- codec failures: 0
- network parse failures: 0
- network schedule failures: 0

This work must recur every 10 ms, before mixing and audio I/O. The codec alone
uses about 2.3 times the available deadline. Packing two frames in each 20 ms
RF packet does not change the required compute rate.

## Consequence

The processor link will carry two 40-byte LC3 frames per 20 ms superframe
between the FG23 radio processor and an audio processor. Its framing must
include sequence, direction, validity/PLC metadata, and queue-overrun counters.

