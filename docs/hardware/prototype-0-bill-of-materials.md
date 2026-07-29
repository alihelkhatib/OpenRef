# Prototype 0 Bill of Materials

**Document ID:** OR-HW-002  
**Revision:** 0.1  
**Status:** Initial purchasing plan; verify current price and availability before purchase

## Required Six-Node Set

| Item | Quantity | Purpose |
|---|---:|---|
| TI CC1352P7 LaunchPad development kit | 6 | Six communication nodes |
| USB data cables compatible with boards | 6 | Power, programming, logging |
| Powered USB hubs | 2 | Multi-node development and automated testing |
| Wired electret or analog headset test assemblies | 6 | Initial audio capture/playback |
| Audio interface or codec breakout boards | 6 | ADC/DAC experimentation |
| Adjustable laboratory supplies or USB power monitors | 2 minimum | Current measurement and fault injection |
| Logic analyzer | 1 | Timing, GPIO, and bus observation |
| Oscilloscope with at least two channels | 1 | Audio and timing measurements |
| Acoustic loopback fixtures or cables | 6 | Repeatable latency testing |
| SMA adapters, attenuators, and coax jumpers | 1 set | Controlled RF tests where board design permits |
| RF shielding boxes or conductive test containers | 2 | Isolation and loss/rejoin testing |
| Headphones with conservative output capability | 6 | Bench monitoring |
| MicroSD or host logging storage | As required | Capturing experiment data |

## Recommended Comparison Set

| Item | Quantity | Purpose |
|---|---:|---|
| Silicon Labs EFR32xG23 868–915 MHz Pro Kit or equivalent mainboard/radio-board combination | 2 | Link, timing, power, and tooling comparison |

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

## Purchase Order

### Batch 1 — Minimal Start

- two TI boards;
- cables;
- one audio input/output path;
- basic current measurement.

Purpose: toolchain, raw packet exchange, timestamping, and audio-loopback feasibility.

### Batch 2 — Six Nodes

Purchase the remaining four TI boards only after Batch 1 demonstrates:

- repeatable programming;
- packet timestamp access;
- arbitrary payload transport;
- stable continuous operation;
- usable logging.

### Batch 3 — Comparison

Purchase two Silicon Labs nodes after the TI baseline has measurable results.

## Safety Note

Prototype audio output shall begin into resistive loads or measurement equipment. Human listening tests require conservative gain, output limiting, and a verified maximum level.
