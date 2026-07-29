# Prototype 0 Platform Matrix

**Document ID:** OR-HW-001  
**Revision:** 0.2  
**Status:** Procurement shortlist

## Lead Platform

| Attribute | Silicon Labs FG23-DK2600A |
|---|---|
| Role | Lead six-node Prototype 0 platform |
| Band | 868–915 MHz |
| Output class | +14 dBm development kit |
| CPU | Arm Cortex-M33 |
| Development advantage | Self-contained, compact board with current availability |
| Radio approach | Proprietary sub-GHz packet experiments |
| Debug | Onboard debug and energy-analysis facilities |
| Main risk | 64 KB-class RAM may constrain later multi-stream codec and mixing work |
| Mitigation | Measure memory and CPU early; keep radio and audio abstractions portable |

## Deferred Comparison Platform

| Attribute | TI LP-CC1352P7-1 |
|---|---|
| Role | Future 915 MHz and 2.4 GHz comparison |
| Bands | 868/915 MHz and 2.4 GHz |
| CPU | Arm Cortex-M4F |
| Development advantage | Dual-band comparison on one board |
| Current issue | Lead-board availability is insufficiently dependable |
| Important restriction | Do not substitute LP-CC1352P7-4; it is the 433 MHz variant |

## Secondary Research Candidates

| Candidate | Purpose | Current Disposition |
|---|---|---|
| Silicon Labs xG23 Pro Kit | Higher-observability radio comparison | Optional |
| Silicon Labs EFR32FG28 | Dual-band modern comparison | Monitor |
| Semtech SX1262 | External FSK transceiver comparison | Defer |
| Nordic nRF52840 | 2.4 GHz proprietary baseline | Optional |
| Nordic nRF9151 | DECT NR+ research | Defer |
| Wi-Fi MCU/platform | High-bandwidth stress comparison | Defer |

## Selection Principle

Prototype 0 hardware is selected for availability, observability, and architectural learning—not miniaturization or lowest production cost.
