# Prototype 1 Pre-Schematic Architecture

**Document ID:** OR-HW-004
**Revision:** 0.1
**Status:** Controlled pre-schematic baseline; component selection gated

The machine-checkable companion contract is
`electrical-interface-contract.json` (OR-HW-005). Run
`python tools/validate_prototype1_interface_contract.py
hardware/prototype1-wearable/electrical-interface-contract.json` before and
after translating these boundaries into CAD.

The sheet-level functional connectivity graph is
`schematic-connectivity.json` (OR-HW-008). It fixes the required power chain,
isolation path, protected audio path, RF boundary, and measurement access while
keeping unselected components explicitly provisional. Cross-check it with:

`python tools/validate_prototype1_connectivity.py
hardware/prototype1-wearable/schematic-connectivity.json
hardware/prototype1-wearable/electrical-interface-contract.json
hardware/prototype1-wearable/fgm230sb-pin-allocation.json`

## Purpose

Define the custom wearable electronics partition, required nets, protection
boundaries, and verification access before CAD capture. This document permits
symbol/library and sheet preparation but does not waive the measured RF, power,
audio, or mechanical gates in the readiness checklist.

## Sheet Partition

| Sheet | Function | Required boundary evidence |
|---|---|---|
| 01 | Protected 1S pack entry, reverse blocking, input limiting, ship/load switch | insertion transient, reverse case, short protection, leakage |
| 02 | Always-on monitor and power sequencing | UV/temperature thresholds, rail order, hard shutdown |
| 03 | FGM230SB FG23 radio/network SiP and debug | secured 114-byte airtime, TX/RX current, final OPN review |
| 04 | RT-class audio processor and debug | LC3/mixer timing, memory, current, peer recovery |
| 05 | Codec, microphone bias, and earpiece output | headset impedance, bias, noise, maximum safe level |
| 06 | Controls, status LED, haptic driver, connector detection | GPIO allocation, wet/glove control mockup |
| 07 | Interprocessor SPI, resets, timing markers, and test points | 8 MHz link and fault-injection validation |
| 08 | 50-ohm RFIO, test boundary, provisional antenna match, and external antenna | enclosure orientation, keepout, body-loss test |

## Named Power Domains

Use unambiguous domain names through schematic and layout:

- `VBAT_PROTECTED`: pack output after pack-internal protection;
- `VSYS_BLOCKED`: after wearable reverse-current and insertion protection;
- `V_ALWAYS_ON`: supervisor, latch, wake, pack sensing;
- `V_RADIO`: FG23 and RF-domain supply;
- `V_AUDIO`: audio-processor I/O and permitted core regulators;
- `V_CODEC`: codec analog/digital and microphone-bias source;
- `V_HAPTIC`: switched vibration load, isolated from analog audio return.

Each switched domain requires enable, power-good where available, local bulk and
high-frequency decoupling, a removable current-measurement link, and accessible
voltage/ground test points. No signal may back-power a disabled domain; use
defined reset states or isolation where the powered side can drive the
unpowered side.

## Processor and Recovery Nets

The fixed processor link is `AUD_SCLK`, `AUD_COPI`, `AUD_CIPO`, `AUD_CSN`,
`AUD_REQ_N`, and `AUD_RESET_N`. Keep source-series footprints on clock and COPI.
Route continuous ground beside the link and avoid crossing codec analog inputs.
`AUD_RESET_N` is driven by the radio processor but requires a physical pull-down
and cross-domain isolation so it remains asserted whenever either processor
domain is unpowered or the FG23 pin is high impedance.

Add `RADIO_RESET_REQ_N` only if the audio processor can drive it safely while
the radio domain is off. The always-on controller owns `RADIO_EN`, `AUDIO_EN`,
and the final hard-shutdown path. Neither application processor may defeat hard
undervoltage or overtemperature shutdown. Both processors expose independent
SWD, reset, UART TX/RX, and timing markers.

## Exposed-Interface Protection

- Battery contacts: mechanical polarization, reverse-current blocking,
  insertion-current control, and transient protection sized after pack choice.
- Headset: low-capacitance ESD at the connector, RF filtering, current-limited
  microphone bias, output series impedance, and connector-detect isolation.
- Controls: ESD-tolerant inputs with defined states during reset and power-off.
- Debug/test: normally unpopulated or fixture-only pads, inaccessible to the
  wearer after final assembly.

Protection parts must be selected against measured signal bandwidth, maximum
fault energy, and enclosure-accessibility classification; footprints alone are
not verification.

## Layout Constraints Carried Into CAD

- Reserve the antenna region before board outline optimization; no battery,
  ground pour, display cable, or headset cable enters its keepout unless the
  selected antenna reference design permits it.
- Separate switching/haptic current loops from microphone input and codec
  reference returns. Join grounds using a continuous reference plane rather
  than narrow split-plane bridges.
- Place radio decoupling and matching at the device/module pins and preserve a
  conducted-test option where the RF architecture allows it.
- Place current links and critical test pads where a fixture can reach them
  with the enclosure service configuration defined.
- Keep crystal, SWD, and high-edge-rate SPI traces out of the microphone input
  region.

## Deterministic Startup and Safe-State Contract

1. Pack insertion powers only the always-on domain.
2. The supervisor validates pack voltage and temperature before enabling loads.
3. Codec output and microphone transmission remain muted.
4. Radio and audio rails start with resets asserted and interface pins benign.
5. Each rail must become valid within its bounded timeout or return to the safe
   state and record a fault.
6. Processors complete authenticated boot and heartbeat exchange.
7. Audio unmutes only after codec initialization, valid configuration load,
   accessory checks, and listening-ceiling application.
8. RF transmission is permitted only after boot-counter advancement and a
   valid authenticated crew session.

## Capture Entry and Release Gates

CAD library preparation and hierarchical sheet capture may begin against this
baseline. Part numbers, board outline, copper geometry, RF matching, regulator
ratings, acoustic gain values, and connector footprints remain provisional
until their named evidence is available. A schematic review may not be called
complete while any readiness item is open or lacks an explicit, risk-owned
waiver in the decision log.
