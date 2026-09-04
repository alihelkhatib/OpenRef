# Prototype 1 Custom PCB Readiness Checklist

## Required Prototype 0 Evidence

- [x] E0-01 toolchain reproduction passed.
- [x] E0-02 one-hour packet pair passed.
- [ ] E0-03 scheduled TX timing measured.
- [ ] Measured packet airtime is compatible with six-node schedule.
- [ ] Current measured for TX, RX, idle, and continuous packet modes.
- [ ] Coordinator/member current estimate exists.
- [x] Radio metadata access confirmed or limitation accepted.
- [x] Initial body/antenna placement risk is bounded for pre-schematic work.
- [x] Audio loopback measurement method exists.

## Architecture Decisions Required

- [x] Wireless path: separate FG23 radio/network processor SoC for Prototype 1.
- [x] Sub-GHz only, 2.4 GHz only, or dual-radio path.
- [x] Audio codec/interface direction.
- [x] Microphone bias/front-end direction.
- [x] Earpiece output architecture and safe-output strategy.
- [x] Battery pack voltage and protection concept.
- [x] Charging inside unit versus external charger.
- [x] Debug/programming connector direction.
- [x] Production-test access-point allocation.

## Mechanical Inputs Required

- [ ] Approximate wearable volume target.
- [ ] Mounting orientation.
- [x] Antenna keepout and placement concept.
- [ ] Battery placement concept.
- [ ] Headset connector placement concept.
- [ ] Control placement concept.
- [x] Minimum sealing objective: normal-use rain and sweat resistance.

## Evidence Basis for Closed Items

| Closed item | Authoritative repository evidence | Scope limit |
|---|---|---|
| E0-01 | `firmware/prototype0/fg23/20260807-e0-01-link-smoke-result.md` | Reproduces the FG23 toolchain; it is not RF-performance evidence. |
| E0-02 | `firmware/prototype0/fg23/20260807-openref-autorole-result.md` | One-hour packet-pair evidence; later payload and security promotion gates remain separate. |
| Radio metadata | `docs/adr/ADR-0004-prototype-0-radio-platform.md` and the FG23 result set | Confirms the development interface, not final production-radio selection. |
| Initial body/antenna risk | `docs/architecture/link-budget-method.md` | Explicitly budgets body shadowing, orientation, enclosure/battery interaction, and required measurement geometries. The 10 dB body term remains a placeholder, so antenna performance is not closed. |
| Audio loopback method | `firmware/prototype0/fg23/20260807-openref-audio-loopback-analysis-plan.md` | Method exists; the physical E0-07 fixture result remains open. |
| Prototype 1 wireless path and sub-GHz band | `docs/program/decision-log.md` DEC-007, `docs/adr/ADR-0004-prototype-0-radio-platform.md`, and `hardware/prototype1-wearable/README.md` | Establishes a separate FG23 radio/network processor for this prototype. It does not select production packaging, module status, matching, or antenna. |
| Audio, microphone, and safe earpiece direction | `docs/interfaces/ICD-001-headset.md` and `docs/adr/ADR-0006-prototype-audio-processor-platform.md` | Establishes analog-headset and separate-processor boundaries; codec part, bias values, impedance, and gain ceiling await measurement. |
| Battery and external charging direction | `docs/power/prototype1-power-tree.md`, `docs/interfaces/ICD-003-charging.md`, and DEC-005 | Establishes a removable protected 1S pack and independent external charger bays; cell, charger, and protection parts remain open. |
| Debug and production-test allocation | `hardware/prototype1-wearable/electrical-interface-allocation.md` | Defines SWD, UART, timing, current-link, rail, and fixture pads; exact connector/fixture geometry remains open. |
| Antenna keepout concept | `hardware/prototype1-wearable/pre-schematic-architecture.md` | Reserves an enclosure-edge RF region free of battery, cable, and disallowed copper. Dimensions require the final radio/antenna and enclosure. |
| Minimum sealing objective | `docs/requirements/srs.md` AUD-017 through AUD-019 and DUR-003 through DUR-005; `docs/interfaces/ICD-001-headset.md` | Normal-use rain, sweat, dirt, and recovery are functional objectives. No IP rating or sealing construction is claimed. |

## Explicit Open Blockers

The nine open items above map one-to-one to
`readiness-inputs-template.json`. `tools/prototype1_readiness_inputs.py`
validates completeness, reviewer attribution, timestamps, and evidence hashes;
it deliberately cannot infer measurements or product decisions.

- E0-03 still needs external timing capture; SDK timestamps do not replace it.
- The 98-byte plaintext payload run does not establish secured 114-byte airtime
  or a six-node slot margin.
- Radio and role-specific current values remain assumptions, not measurements.
- The body-loss framework does not select antenna type, matching, or keepout
  dimensions without representative enclosure measurements.
- Wearable volume, mounting orientation, battery location, connector location,
  and control placement require mechanical mockups or product-owner inputs.
- A rain/sweat objective is not an enclosure rating; sealing strategy and
  ingress validation remain later physical gates.

## Review Gate

Start custom PCB schematic only when all required evidence exists or a decision
log entry records why a missing item is intentionally waived.
