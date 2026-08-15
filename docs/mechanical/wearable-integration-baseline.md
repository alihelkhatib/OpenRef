# Prototype 1 Wearable Integration Baseline

**Document ID:** OR-HW-010  
**Revision:** 0.1  
**Status:** Controlled interface baseline; physical placement inputs pending

## Purpose

Define the mechanical boundaries that must be settled before the PCB outline,
antenna placement, connector footprints, and enclosure can be released. The
machine-readable authority is
`hardware/prototype1-wearable/wearable-mechanical-contract.json` (OR-HW-009).

The contract intentionally leaves dimensions and placements unset. Guessing a
wear location or enclosure size would constrain antenna performance, controls,
battery retention, and cable loads without user or mockup evidence.

## Fixed Constraints

- The antenna volume excludes the battery, headset cable, debug access,
  switching-power loop, and haptic actuator.
- The analog-audio region excludes switching, haptic, and high-edge-rate
  digital routing.
- The removable pack is polarized, independently retained, sealed at its
  boundary, and charged outside the wearable.
- Headset cable load is transferred into enclosure strain relief rather than
  the PCB solder joint.
- User controls remain sealed and require wet-hand, glove, motion, and
  accidental-activation testing.
- Debug and production-test contacts remain fixture-accessible in the service
  configuration but inaccessible to the wearer.
- Normal and foreseeable damaged configurations may not expose sharp edges or
  allow the battery to become a projectile.

## Required Physical Decisions

Before mechanical release, record the wear location and orientation, positive
X/Y/Z envelope, target mass, minimum sealing objective, and service
configuration. Select explicit antenna, battery, headset connector, control,
and status-visibility locations using a representative body-worn mockup.

Run:

```text
python tools/validate_wearable_mechanical_contract.py \
  hardware/prototype1-wearable/wearable-mechanical-contract.json \
  --require-release
```

Without `--require-release`, the tool validates that the incomplete baseline is
safe and internally consistent while listing the genuine physical-input
blockers. Strict mode fails until every decision is populated.

## Verification Required After Integration

The final assembly must produce AV-015 rain/sweat/mud, AV-016 drop and battery
retention, AV-017 wet/glove controls, AV-018 headset fault/wet leakage, AV-019
listening-level, and AV-036 mount/strain-relief/damaged-edge evidence. Passing a
bare-PCB electrical test cannot substitute for these enclosure-level tests.
