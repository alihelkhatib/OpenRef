# ADR-0004: Prototype 0 Radio Platform

**Status:** Accepted for Prototype 0  
**Date:** 2026-07-29

## Decision

Use the Texas Instruments CC1352P7 LaunchPad as the lead development platform for OpenRef Prototype 0.

Purchase a smaller Silicon Labs EFR32FG23 evaluation set only as a comparative radio platform if budget permits.

This decision selects a development platform for experimentation. It does not select the final production silicon, radio protocol, antenna, transmit power, or certified module.

## Rationale

The CC1352P7 platform provides:

- sub-1 GHz and 2.4 GHz radios on one development platform;
- proprietary-radio support;
- an integrated high-power amplifier;
- an onboard debugger;
- accessible I/O for audio and test instrumentation;
- sufficient flash for experimental protocol, logging, and security work;
- a practical path to compare 915 MHz and 2.4 GHz without rebuilding the entire prototype.

This directly supports the open architecture question: whether the body-worn and coexistence benefits of 902–928 MHz outweigh antenna and bandwidth costs.

## Comparison Platform

The EFR32FG23 remains the preferred comparison because it offers:

- a modern Cortex-M33 implementation;
- proprietary sub-GHz tooling;
- strong security features;
- dedicated 868–915 MHz development hardware;
- an independent vendor ecosystem against which TI-specific results can be checked.

## Not Selected

### Bluetooth-only platform

Not selected because Prototype 0 must control medium access, multicast behavior, timing, and recovery rather than inherit a consumer audio topology.

### Wi-Fi-only platform

Not selected because its high throughput does not offset contention, power, and body-worn coexistence uncertainty for the primary experiment.

### LoRa as the voice waveform

Not selected because the long-airtime, low-rate operating modes are unsuitable for six simultaneous interactive voice sources.

### Semtech SX1262 as lead platform

The SX1262 supports FSK as well as LoRa, but it is a radio transceiver rather than the most direct integrated six-node development platform. It may be revisited if the integrated wireless-MCU candidates cannot meet capacity or timing requirements.

### Nordic nRF9151

Not selected for Prototype 0 because its 915 MHz direction is tied to cellular/DECT NR+ architecture and introduces a materially different ecosystem, complexity level, and likely cost profile.

## Consequences

- initial firmware experiments use the TI toolchain and radio APIs;
- protocol abstractions shall prevent permanent coupling to TI packet structures;
- the same lead platform shall be tested at sub-GHz and 2.4 GHz where practical;
- production hardware selection remains open until measured Prototype 0 results exist;
- all range claims remain invalid until body-worn antenna testing.

## Reconsideration Triggers

Reopen this decision if:

- six continuous sources cannot be scheduled with adequate margin;
- radio timing APIs are insufficiently deterministic;
- codec and mixing workload exceeds available compute or memory;
- the antenna requirement is incompatible with the wearable;
- development tooling prevents reliable measurement;
- current consumption makes eight-hour endurance implausible.
