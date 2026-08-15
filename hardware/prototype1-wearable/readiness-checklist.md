# Prototype 1 Custom PCB Readiness Checklist

## Required Prototype 0 Evidence

- [x] E0-01 toolchain reproduction passed.
- [x] E0-02 one-hour packet pair passed.
- [ ] E0-03 scheduled TX timing measured.
- [ ] Measured packet airtime is compatible with six-node schedule.
- [ ] Current measured for TX, RX, idle, and continuous packet modes.
- [ ] Coordinator/member current estimate exists.
- [x] Radio metadata access confirmed or limitation accepted.
- [ ] Initial body/antenna placement risk is understood.
- [x] Audio loopback measurement method exists.

## Architecture Decisions Required

- [x] Wireless SiP path selected for Prototype 1; FGM230S is explicitly uncertified and still requires product approval testing.
- [x] Sub-GHz only, 2.4 GHz only, or dual-radio path.
- [x] Audio codec/interface direction.
- [x] Microphone bias/front-end direction.
- [x] Earpiece output architecture and safe-output strategy.
- [x] Battery pack voltage and protection concept.
- [x] Charging inside unit versus external charger.
- [x] Debug/programming connector direction.
- [x] Production-test access-point allocation.

## Mechanical Inputs Required

The controlled unset values and fixed safety constraints are in OR-HW-009;
strict validation must pass before board-outline release.

- [ ] Approximate wearable volume target.
- [ ] Mounting orientation.
- [ ] Antenna keepout and placement concept.
- [ ] Battery placement concept.
- [ ] Headset connector placement concept.
- [ ] Control placement concept.
- [ ] Minimum sealing objective.
- [x] Battery retention, headset strain relief, service-access, zone-separation,
  damaged-edge, and enclosure-level verification constraints are controlled.

## CAD Library Intake

- [x] All FGM230SB package pads have controlled net, direction, safe-state, and
  electrical-class assignments.
- [x] SPI, UART, ADC, LFXO, and fixed debug routes are validated against the
  installed production FGM230SB27HGN SDK metadata.
- [x] EDA-neutral symbol pin table is reproducibly generated from the controlled
  allocation.
- [x] Manufacturer land-pattern, stencil, paste, and assembly acceptance values
  are captured in a controlled requirement document.
- [x] Power, isolated processor link, protected headset path, RF boundary, and
  test access are reconciled in a machine-validated connectivity graph.
- [ ] Native EDA symbol and footprint parse without warnings.
- [ ] Native EDA electrical-rule and design-rule checks pass.
- [x] Footprint geometry is visually and dimensionally checked against the
  manufacturer package drawing.

## Review Gate

Start custom PCB schematic only when all required evidence exists or a decision
log entry records why a missing item is intentionally waived.
