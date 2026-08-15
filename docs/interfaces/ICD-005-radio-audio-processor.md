# Radio-to-Audio Processor Interface

**Document ID:** OR-ICD-005  
**Revision:** 0.2  
**Status:** Prototype baseline

## Purpose

Define the deterministic internal link between the EFR32FG23 radio/network
processor and the audio processor. The interface transports encoded audio; raw
PCM never crosses this boundary in normal operation.

## Electrical Baseline

- full-duplex SPI, FG23 as controller;
- 8 MHz minimum clock, mode selected during schematic capture;
- one active-low request line from the audio processor;
- one active-low reset line controlled by the FG23;
- shared logic supply and ground, with series-resistor footprints on clock and
  data lines;
- no connector in the production wearable; test pads remain available.

At 8 MHz, one 98-byte transaction takes 98 us. Five remote transfers and one
local transfer require 588 us per 20 ms superframe, or 2.94% raw bus occupancy.
This excludes chip-select gaps but leaves substantial deterministic margin.

## Fixed Transaction

Every transaction is exactly 98 bytes. Multi-byte values are little-endian.

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 2 | Magic `0x414F` |
| 2 | 1 | Version `1` |
| 3 | 1 | Kind: local audio, remote audio, or status |
| 4 | 1 | Source node ID; zero only for status |
| 5 | 1 | Flags |
| 6 | 2 | 20 ms source sequence |
| 8 | 4 | Low 32 bits of source timestamp, microseconds |
| 12 | 2 | Payload length, fixed at 80 |
| 14 | 1 | Producer queue depth, 0 through 4 |
| 15 | 1 | Reserved, zero |
| 16 | 80 | Two consecutive 40-byte LC3 frames |
| 96 | 2 | CRC-16/CCITT-FALSE over bytes 0 through 95 |

Flag bit 0 validates the first 10 ms codec frame, bit 1 validates the second,
and bit 2 marks a discontinuity. An invalid half-frame invokes decoder packet
loss concealment; it is never replaced with stale audio.

## Queue and Failure Rules

- each direction has a statically allocated four-entry queue;
- producers never block the audio or radio deadline;
- on overflow, the oldest queued frame is discarded because newer speech is
  more useful than late speech;
- pushes, pops, overruns, CRC failures, sequence gaps, and resets are observable;
- malformed frames are discarded without changing the last accepted sequence;
- repeated CRC or liveness failures reset only the peer processor, not crew
  identity or network credentials;
- status traffic is lower priority than audio and cannot occupy an audio slot.

The vendor-independent wire codec and queue are implemented in
`firmware/common/openref_audio_link.h/.c`.

The portable transaction policy is implemented in
`firmware/common/openref_audio_transport.h/.c`. It gives queued audio priority
over status, replaces superseded pending status rather than building a status
backlog, and emits a valid idle status frame whenever a full-duplex transaction
has no application payload. `AUDIO_REQn` is asserted only while queued audio or
an explicit status update is pending. Receive processing authenticates the
frame CRC before changing sequence state, marks discontinuities on source
sequence gaps, and exposes malformed-frame, gap, overflow, and transaction
counters to target diagnostics.

## BRD2600A Bench Allocation

For the RT595 validation bench, the provisional FG23 allocation is PA7/COPI,
PA8/CIPO, PB0/SCLK, PB1/CSn, PB2/AUDIO_REQn, and PB3/AUDIO_RESETn. These pads
avoid PA1/SWCLK and PA2/SWDIO so firmware remains debuggable. Board peripherals
sharing the selected pads must be disabled. Both development boards remain
independently USB-powered with ground and logic connected; their supply rails
must not be tied together.
