# ADR-0007: Prototype 1 Radio SiP Baseline

**Status:** Accepted for Prototype 1 schematic baseline  
**Date:** 2026-08-14  
**Decision owner:** Systems engineering

## Decision

Use `FGM230SB27HGN3` (Secure Vault High, +14 dBm) as the preferred Prototype 1
radio/network-processor SiP. Retain the direct `EFR32FG23B` QFN path as the
cost/size optimization alternative for a later prototype or production design.

This decision authorizes symbol, footprint, power, debug, and 50-ohm RF-boundary
capture. It does not select an antenna, approve RF geometry, claim range,
approve transmit power, or complete FCC authorization.

## Evidence

Silicon Labs specifies FGM230S as a 6.5 x 6.5 mm SiP with 512 kB flash, 64 kB
RAM, 868/915 MHz operation, and up to +14 dBm output. The `B` variant provides
Secure Vault High. The SiP integrates the EFR32FG23, 39 MHz crystal, DCDC LC,
supply filtering/decoupling, and RF matching, while exposing a 50-ohm `RFIO`
pin for an external antenna. Typical published 916 MHz current is 4.1 mA RX,
20.8 mA TX at +10 dBm, and 30.0 mA TX at +14 dBm. These values are allocations,
not OpenRef measurements.

The manufacturer explicitly identifies FGM230S as an uncertified module.
OpenRef therefore still requires product-level emissions, antenna, body-loading,
and FCC compliance work.

Official sources:

- <https://www.silabs.com/wireless/proprietary/fgm230s-sub-ghz-sip-modules>
- <https://www.silabs.com/documents/public/data-sheets/fgm230s-datasheet.pdf>
- <https://www.silabs.com/documents/public/data-sheets/efr32fg23-datasheet.pdf>

## Rationale

Prototype 1 should reduce simultaneous unknowns. The SiP preserves the proven
FG23 software and radio family while removing first-spin crystal, DCDC, and
device-side RF-match implementation risk. Secure Vault High matches the current
key-management, attestation, secure-debug, and lifecycle architecture. Its 34
GPIOs are compatible with the pre-schematic interface allocation.

The SiP is larger and, at currently published 1,000-unit pricing, more expensive
than the bare SoC. It does not remove external antenna design or regulatory
testing. Those costs are accepted for the first custom electronics prototype,
where bring-up risk is more important than final unit optimization.

## Required Schematic Treatment

- Use the manufacturer land pattern and assembly guidance; do not redraw from
  memory.
- Connect all required ground pads directly to a solid plane.
- Route `RFIO` as a controlled 50-ohm line to a configurable antenna boundary.
- Include a conducted-test option and a provisional external antenna matching
  network permitted by the reference design.
- Preserve SWD, reset, UART logging, PTI/timing markers, and domain current link.
- Treat published current as `datasheet` evidence in the power model until
  replaced by OpenRef measurements.

## Exit and Reconsideration Triggers

Reopen the choice if measured body-worn RF performance, secured 114-byte
airtime, current/endurance, package assembly yield, supply continuity, GPIO
allocation, BOM target, or enclosure antenna volume fails its gate. A production
move to bare EFR32FG23 requires a fresh RF layout, matching, crystal, DCDC,
manufacturing, and compliance review rather than a footprint substitution.
