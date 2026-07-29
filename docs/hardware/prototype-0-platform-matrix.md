# Prototype 0 Platform Matrix

**Document ID:** OR-HW-001  
**Revision:** 0.1  
**Status:** Procurement shortlist

## Lead Platform

| Attribute | TI CC1352P7 LaunchPad |
|---|---|
| Role | Lead six-node Prototype 0 platform |
| Bands | Sub-1 GHz and 2.4 GHz |
| CPU | Arm Cortex-M4F |
| Development advantage | One board supports both primary band experiments |
| Radio approach | Proprietary or supported standardized PHY/MAC experiments |
| Debug | Onboard XDS110 |
| Antenna support | Development-board sub-GHz and 2.4 GHz support |
| Main risk | Application CPU and memory may eventually constrain multi-stream audio |
| Mitigation | Measure early; permit external audio processor or later SoC change |

## Comparison Platform

| Attribute | Silicon Labs EFR32FG23 |
|---|---|
| Role | Independent sub-GHz comparison |
| Band | Sub-GHz, including 868–915 MHz development options |
| CPU | Arm Cortex-M33 |
| Development advantage | Strong proprietary-radio tooling and security architecture |
| Debug | Wireless starter/pro kit ecosystem |
| Main risk | Higher cost for a six-node comparative set |
| Mitigation | Begin with two nodes for link, timing, and tooling comparison |

## Secondary Research Candidates

| Candidate | Purpose | Current Disposition |
|---|---|---|
| Silicon Labs EFR32FG28 | Dual-band modern comparison | Monitor; not required for initial purchase |
| Semtech SX1262 | External FSK transceiver comparison | Defer |
| Nordic nRF52840 | 2.4 GHz proprietary baseline | Optional only |
| Nordic nRF9151 | DECT NR+ research | Defer |
| Wi-Fi MCU/platform | High-bandwidth stress comparison | Defer |

## Selection Principle

Prototype 0 hardware is selected for observability and architectural learning, not miniaturization or lowest production cost.
