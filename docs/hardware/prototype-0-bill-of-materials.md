# Prototype 0 Bill of Materials

**Document ID:** OR-HW-002  
**Revision:** 0.2  
**Status:** Initial purchasing plan; verify price and availability immediately before purchase

## Required Six-Node Set

| Item | Quantity | Purpose |
|---|---:|---|
| Silicon Labs FG23-DK2600A development kit | 6 total | Six communication nodes |
| USB data cables compatible with boards | 6 | Power, programming, logging |
| Powered USB hubs | 2 | Multi-node development and automated testing |
| Wired electret or analog headset test assemblies | 6 | Initial audio capture/playback |
| Audio interface or codec breakout boards | 6 | ADC/DAC experimentation |
| USB power analyzer or suitable current monitor | 2 minimum | Current measurement and fault injection |
| Logic analyzer | 1 | Timing, GPIO, and bus observation |
| Oscilloscope with at least two channels | 1 | Audio and timing measurements |
| Acoustic loopback fixtures or cables | 6 | Repeatable latency testing |
| RF attenuators and coax accessories | 1 set | Controlled RF tests where supported |
| RF shielding boxes or conductive test containers | 2 | Isolation and loss/rejoin testing |
| Resistive audio loads | 6 | Safe initial audio-output testing |

## Purchase Order

### Batch 1 — Entry-Test Pair

Purchase:

- two `FG23-DK2600A` boards;
- two suitable USB data cables;
- one basic current-measurement path;
- one audio input/output test path.

Purpose:

- reproduce the toolchain;
- establish raw packet exchange;
- validate timestamps and scheduled transmission;
- run continuous one-hour transport;
- establish audio-loopback measurement.

### Batch 2 — Six-Node Expansion

Purchase four additional matching `FG23-DK2600A` boards only after Batch 1 demonstrates:

- repeatable programming from repository instructions;
- packet timestamp access;
- arbitrary payload transport;
- scheduled transmission behavior;
- stable continuous operation;
- usable logs and GPIO timing markers.

### Batch 3 — Vendor/Band Comparison

Purchase one or two `LP-CC1352P7-1` boards only when readily available and only after the six-node FG23 baseline has measurable results.

Do not purchase `LP-CC1352P7-4` for the 915 MHz experiment.

## Existing Equipment Can Substitute

Do not buy duplicates if already available:

- bench power supply;
- oscilloscope;
- logic analyzer;
- RF attenuators;
- audio interface;
- powered hubs;
- measurement microphone;
- sound-level meter.

## Safety Note

Prototype audio output shall begin into resistive loads or measurement equipment. Human listening tests require conservative gain, output limiting, and a verified maximum level.
