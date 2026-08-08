# Prototype 1 Custom PCB Readiness Checklist

## Required Prototype 0 Evidence

- [ ] E0-01 toolchain reproduction passed.
- [ ] E0-02 one-hour packet pair passed.
- [ ] E0-03 scheduled TX timing measured.
- [ ] Measured packet airtime is compatible with six-node schedule.
- [ ] Current measured for TX, RX, idle, and continuous packet modes.
- [ ] Coordinator/member current estimate exists.
- [ ] Radio metadata access confirmed or limitation accepted.
- [ ] Initial body/antenna placement risk is understood.
- [ ] Audio loopback measurement method exists.

## Architecture Decisions Required

- [ ] Wireless SoC, certified module, or external radio transceiver path.
- [ ] Sub-GHz only, 2.4 GHz only, or dual-radio path.
- [ ] Audio codec/interface direction.
- [ ] Microphone bias/front-end direction.
- [ ] Earpiece output architecture and safe-output strategy.
- [ ] Battery pack voltage and protection concept.
- [ ] Charging inside unit versus external charger.
- [ ] Debug/programming connector.
- [ ] Production-test access points.

## Mechanical Inputs Required

- [ ] Approximate wearable volume target.
- [ ] Mounting orientation.
- [ ] Antenna keepout and placement concept.
- [ ] Battery placement concept.
- [ ] Headset connector placement concept.
- [ ] Control placement concept.
- [ ] Minimum sealing objective.

## Review Gate

Start custom PCB schematic only when all required evidence exists or a decision
log entry records why a missing item is intentionally waived.
