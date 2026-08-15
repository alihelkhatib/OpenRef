# Audio Pipeline Architecture

**Document ID:** OR-ARC-010  
**Revision:** 0.1  
**Status:** Baseline functional architecture

## End-to-End Path

1. Headset microphone
2. Input protection and bias
3. Analog gain and anti-alias filtering
4. Analog-to-digital conversion
5. DC removal and level normalization
6. Wind and low-frequency suppression
7. Voice encoding
8. Packetization and authentication
9. Radio scheduling and transmission
10. Receive validation and de-jittering
11. Packet-loss concealment
12. Multi-user mixing
13. Output limiting
14. Digital-to-analog conversion
15. Headset earpiece

## Latency Allocation

The one-way target is 120 ms or less.

Initial allocation:

| Stage | Budget |
|---|---:|
| Microphone and capture framing | 10 ms |
| Audio processing and encoding | 15 ms |
| Packetization wait | 20 ms |
| Radio access and transport | 30 ms |
| Receive jitter margin | 25 ms |
| Decode, mix, and playback | 15 ms |
| Engineering reserve | 5 ms |

The allocation is provisional. No individual stage may consume its full budget by default.

## Processing Principles

- critical audio processing shall use bounded execution time;
- no dynamic memory allocation in the steady-state audio path;
- all signal levels shall use explicit headroom;
- clipping shall be detected and observable in diagnostics;
- packet-loss concealment shall degrade intelligibility gradually;
- stale audio shall be discarded rather than played late;
- diagnostic capture shall never block live audio.

## Multi-Talker Mixing

The mixer shall:

- support at least five remote sources plus local sidetone if enabled;
- prevent arithmetic overflow;
- preserve intelligibility during simultaneous speech;
- apply gain normalization or limiting without pumping;
- avoid allowing one failed source to dominate the mix.

The portable Prototype 0 mixer processes fixed 160-sample (10 ms at 16 kHz)
blocks from five remote decoders. Each source has an explicit Q15 gain. A
block-peak limiter applies immediate attack and controlled release, and reports
limited blocks, pre-limit peak, and any final saturation. Missing sources are
excluded using a validity mask; stale audio is never substituted. The
implementation is `firmware/audio_processor/common/openref_audio_mixer.h/.c`.

Receive playout uses a four-packet static queue per source. Each 20 ms radio
payload is split into two independently valid 10 ms codec frames. Sequence gaps
or invalid halves generate explicit PLC requests, while duplicate and stale
packets are discarded. The implementation reports accepted, duplicate, stale,
overrun, delivered, and PLC counts per source in
`firmware/audio_processor/common/openref_audio_playout.h/.c`.

## Wind and Handling Noise

The baseline approach shall combine:

- mechanical microphone protection;
- high-pass filtering;
- level-dependent low-frequency suppression;
- overload recovery;
- optional voice activity information for diagnostics, not admission control.

Voice transmission shall not depend on a voice-activity detector because clipped, shouted, or wind-affected speech must still be carried.
