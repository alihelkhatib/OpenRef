# Wearable Power Supervisor

**Document ID:** OR-PWR-004
**Revision:** 0.1
**Status:** Portable state machine implemented; calibration pending

## Purpose

The supervisor translates validated pack measurements and an estimated remaining
runtime into deterministic user-warning and shutdown actions. It is independent
of the eventual fuel-gauge, ADC, regulator, and processor SDK.

The implementation is
`firmware/system/common/openref_power_supervisor.h/.c`.

## Required input

Each sample supplies:

- pack-present status;
- measurement-valid status;
- estimated remaining runtime in minutes;
- loaded battery voltage in millivolts;
- pack temperature in hundredths of a degree Celsius;
- a monotonic millisecond timestamp.

The runtime estimate must come from a calibrated fuel gauge or discharge model.
Battery voltage alone is not treated as a state-of-charge estimate, especially
during radio and headphone current bursts.

## State behavior

| Condition | Behavior |
|---|---|
| Pack absent | Mute and request shutdown; clear the shutdown latch |
| Normal estimate | Normal operation |
| At or below low threshold | Persistent low-runtime warning |
| At or below critical threshold | Critical warning and load reduction |
| Critical grace expires | Mute and request deterministic shutdown |
| Hard undervoltage | Immediate latched mute and shutdown |
| Overtemperature | Immediate latched mute and shutdown |
| Invalid measurement | Fail-closed latched mute and shutdown |

Runtime thresholds use configurable hysteresis. A latched shutdown can only be
cleared by observing pack removal, preventing a sagging or overheated pack from
cycling the product repeatedly.

## Prototype calibration values

The tests exercise a 45-minute low warning, 10-minute critical threshold,
5-minute hysteresis, 10-minute critical grace, 3.0 V hard cutoff, and 60 degrees
Celsius maximum pack temperature. These are executable test assumptions, not
approved cell limits. The selected protected pack specification and measured
loaded discharge curves must supply production values.

## Promotion tests

1. Replay a measured full discharge trace including scheduled TX bursts.
2. Verify the low warning begins with at least 45 minutes measured operation
   remaining at the aged-pack and low-temperature corner.
3. Verify the critical warning persists for the configured grace period without
   violating the pack minimum voltage.
4. Inject open, shorted, and implausible temperature/voltage measurements.
5. Remove and reinsert the pack at every state and during flash writes.
6. Verify audio mutes before regulators or processors enter undefined operation.
