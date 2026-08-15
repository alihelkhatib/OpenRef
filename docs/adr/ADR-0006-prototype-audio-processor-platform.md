# ADR-0006: Prototype Audio Processor Platform

**Status:** Accepted for bench prototype; production processor not selected  
**Date:** 2026-08-14

## Context

The EFR32FG23 hardware benchmark required about 23.04 ms for one LC3 encode and
five LC3 decodes that must complete every 10 ms. Radio scheduling remained
healthy, but the codec workload alone exceeded the deadline. OpenRef therefore
needs a separate audio processor for codec, mixing, microphone capture, and
headphone playback.

## Decision

Use the **MIMXRT595-EVK** for the next audio bench prototype. It combines a
200 MHz Cortex-M33, a 200 MHz Cadence Fusion F1 DSP, 5 MB internal SRAM, dual
digital microphones, an audio codec with headphone output, expansion
interfaces, and onboard debug support.

Official platform source:
<https://www.nxp.com/design/design-center/development-boards-and-designs/i-mx-evaluation-and-development-boards/i-mx-rt595-evaluation-kit%3AMIMXRT595-EVK>

This selects a validation platform, not the production MCU. Production
selection still requires measured timing, power, package/layout, toolchain,
cost, lifecycle, and supply evidence.

## Alternative

The NUCLEO-H563ZI is the fallback. STM32H563 provides a 250 MHz Cortex-M33,
640 KB RAM, 2 MB flash, SPI, and I2S, but its Nucleo board needs external
microphone and headphone hardware before full-chain testing.

Official sources:

- <https://www.st.com/en/microcontrollers-microprocessors/stm32h563zi.html>
- <https://www.st.com/en/evaluation-tools/nucleo-h563zi.html>

The single-FG23 alternative is rejected for six-participant audio by direct
timing evidence. The FG23 remains the radio/network processor.

## Exit Tests

The RT595 prototype is accepted only after it demonstrates:

1. one LC3 encode plus five decodes, mixing, and audio I/O inside 8 ms of each
   10 ms interval;
2. bounded stack and static memory with at least 20% capacity margin;
3. continuous microphone-to-headphone and encoded loopback;
4. the fixed 98-byte link at 8 MHz or faster with CRC, sequence-gap, reset,
   and overflow fault injection;
5. no stale playback and correct PLC for either missing half-frame;
6. measured active and sleep current for the power trade study.

