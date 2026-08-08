# ADR-0004: Prototype 0 Radio Platform

**Status:** Accepted for Prototype 0  
**Date:** 2026-07-29  
**Revision:** 0.2 — procurement correction

## Decision

Use the Silicon Labs `FG23-DK2600A` 868–915 MHz +14 dBm development kit as the lead development platform for OpenRef Prototype 0.

Begin with two boards. Purchase the remaining four boards only after the Prototype 0 entry tests demonstrate deterministic packet timing, continuous transport, usable diagnostics, and stable development tooling.

Retain the Texas Instruments `LP-CC1352P7-1` as a future comparison platform when it is readily available. Do not substitute the `LP-CC1352P7-4`, which is the 433 MHz variant.

This decision selects a development platform for experimentation. It does not select the final production silicon, radio protocol, antenna, transmit power, or certified module.

## Rationale

The FG23-DK2600A provides:

- a development platform specifically covering 868–915 MHz;
- proprietary sub-GHz protocol support;
- an Arm Cortex-M33 wireless SoC;
- onboard debugging and energy-analysis support;
- a compact board that can later support preliminary body-placement experiments;
- current direct and distributor availability;
- a lower-risk path to purchasing six identical nodes.

The earlier TI recommendation depended on a board that was not readily available. Procurement continuity is an engineering requirement for a repeatable six-node prototype.

## Comparison Platform

The TI `LP-CC1352P7-1` remains technically valuable because it supports 868/915 MHz and 2.4 GHz on one platform. It may be purchased later to compare vendor radio timing and to test 2.4 GHz without changing processor families.

## Not Selected

### TI LP-CC1352P7-4

Not selected because its sub-GHz RF design is for 433 MHz rather than the U.S. 902–928 MHz target band.

### Bluetooth-only platform

Not selected because Prototype 0 must control medium access, multicast behavior, timing, and recovery rather than inherit a consumer audio topology.

### Wi-Fi-only platform

Not selected because high throughput does not offset contention, power, and body-worn coexistence uncertainty for the primary experiment.

See [ADR-0005](ADR-0005-esp32-wroom-role.md) for the specific ESP32-WROOM role decision.

### LoRa as the voice waveform

Not selected because long-airtime, low-rate modes are unsuitable for six simultaneous interactive voice sources.

## Consequences

- initial firmware experiments use Simplicity Studio, Gecko SDK, and Silicon Labs radio APIs;
- protocol abstractions shall prevent permanent coupling to Silicon Labs packet structures;
- 2.4 GHz comparison moves to a later optional experiment;
- purchasing occurs in two-board and four-board gates;
- production hardware selection remains open until measured Prototype 0 results exist;
- all range claims remain invalid until body-worn antenna testing.

## Reconsideration Triggers

Reopen this decision if:

- two boards cannot sustain deterministic continuous packet transport;
- the radio API cannot expose required timing and metadata;
- six continuous sources cannot be scheduled with adequate margin;
- codec and mixing workload exceeds available compute or memory;
- current consumption makes eight-hour endurance implausible;
- four additional matching boards cannot be procured.
