# Voice Codec Trade Study

**Document ID:** OR-ARC-011  
**Revision:** 0.1  
**Status:** LC3 first-candidate selected for embedded benchmark

## Required Characteristics

The selected codec must provide:

- intelligible speech in wind and crowd noise;
- low algorithmic delay;
- moderate bitrate;
- bounded CPU and memory use;
- resilience to packet loss;
- implementation licensing compatible with an open product;
- deterministic operation on the selected embedded platform.

## Candidate Classes

### Narrowband Speech Codec

Advantages:

- low bitrate;
- low radio airtime;
- modest processing.

Disadvantages:

- reduced consonant clarity;
- less natural speech;
- weaker robustness when several voices overlap.

### Wideband Speech Codec

Advantages:

- improved intelligibility;
- better differentiation of overlapping voices;
- more natural monitoring.

Disadvantages:

- higher bitrate;
- greater processing and memory demands.

### General-Purpose Low-Delay Audio Codec

Advantages:

- strong quality;
- flexible rate and packet-loss features.

Disadvantages:

- potentially excessive complexity;
- licensing or implementation concerns;
- may require more capable hardware than necessary.

## Evaluation Points

Each candidate shall be tested at:

- 10 ms and 20 ms packetization;
- 16, 24, and 32 kbps where supported;
- 0%, 5%, 10%, 20%, and burst packet loss;
- single speaker;
- two simultaneous speakers;
- five simultaneous remote speakers;
- representative wind and crowd recordings.

## Selection Rule

Codec selection shall be based on intelligibility, latency, resource use, packet-loss behavior, and legal suitability.

Perceived fidelity alone is not sufficient.

## 2026-08-14 Preliminary Down-Selection

The first embedded candidate is Bluetooth LC3 configured for mono, 16 kHz
wideband speech, 10 ms frames, and 32 kbit/s. Two 40-byte codec frames are
carried in each 20 ms OpenRef radio opportunity, for 80 encoded bytes per
source packet. LC3 explicitly supports 7.5 ms and 10 ms frames, and the
Bluetooth Basic Audio Profile defines the 16 kHz/10 ms/40-byte configuration.

The reasons for testing LC3 first are:

- its frame size and delay are deterministic;
- it was designed for low-complexity communication audio;
- Google's Apache-2.0 `liblc3` provides static-memory encoder and decoder APIs;
- it includes packet-loss decode behavior;
- its measured state footprint fits the current FG23 prototype better than
  expected.

An ARM Cortex-M33 type-size probe against `google/liblc3` measured:

| State | Bytes |
|---|---:|
| 16 kHz encoder | 2,600 |
| 16 kHz decoder | 3,144 |
| One encoder plus five decoders | 18,320 |

The current FG23 development device reports 512 kB flash and 64 kB SRAM. A
2026-08-14 linked hardware benchmark measured one encode plus five decodes at
about 23.04 ms per 10 ms frame interval. The codec ran without errors alongside
the radio network, but cannot meet the real-time six-participant deadline on a
single FG23. The product therefore uses the FG23 as the radio/network processor
and assigns codec, mixing, and audio I/O to a separate audio processor. See
`firmware/prototype0/fg23/20260814-openref-lc3-benchmark-result.md`.

Opus remains the comparison candidate at mono, 16 kHz, 20 ms, 24 kbit/s, and
complexity 0-2. Its 60-byte nominal frame fits the already demonstrated radio
packet, and its fixed-point implementation supports preallocated state. It is
not selected yet because five simultaneous decoder states and embedded cycle
cost must be measured on the actual FG23 build.

Primary references:

- <https://www.bluetooth.com/specifications/specs/low-complexity-communication-codec-1-0-1/>
- <https://github.com/google/liblc3>
- <https://opus-codec.org/docs/>
- <https://www.silabs.com/documents/public/data-sheets/efr32fg23-datasheet.pdf>

## Selection and Remaining Validation

LC3 is the Prototype 0 transport codec at 16 kHz mono, 10 ms, and 40 bytes per
frame. The remaining validation moves to the audio-processor prototype:

- one encode, five decodes, mixing, and I/O within each 10 ms deadline;
- bounded stack and total memory with at least 20% engineering margin;
- two-frame packet packing into an 80-byte payload;
- acceptable speech under isolated and burst packet loss;
- a bounded, observable link between the audio processor and FG23;
- no radio-slot deadline failures while processor-link traffic is active.
