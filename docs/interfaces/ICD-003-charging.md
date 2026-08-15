# OR-ICD-003: Charging Interface

**Revision:** 0.2
**Status:** Portable safety policy implemented; electrical design pending

## Required Behaviors

Charging shall:

- operate from a commonly available U.S. low-voltage power source;
- prevent unsafe charging under temperature, voltage, or battery-fault conditions;
- clearly indicate charging, complete, and fault states;
- avoid dependence on internet services or accounts;
- support charging logistics for a six-person crew;
- prevent a single failed charging position from disabling all other positions where practical.

Charging during active match communication is not assumed and requires a later explicit decision.

## Independent Bay Safety Policy

Each physical bay owns an independent `openref_charge_supervisor` instance.
Pack insertion enters precheck with charging disabled. Charging is enabled only
after pack identity, sensor validity, temperature, pack voltage, and charger IC
status are valid. Charge completion disables charging and records a completed
cycle. A configurable maximum active-charge interval prevents indefinite
charging if completion is never observed.

Invalid identity, failed sensing, out-of-range temperature or voltage, charger
fault, timeout, or monotonic-clock rollback disables the bay and latches its
fault until pack removal. A healthy bay never depends on another bay's state,
which preserves charging capacity after a single-position failure. State and
fault-mask transitions are available for `OPENREF_EVENT_CHARGE_STATE` logging
and per-bay indicators.

`firmware/system/common/openref_charge_supervisor.h/.c` implements this policy.
Temperature/voltage/time limits in unit tests are illustrative only. Production
values require the selected cell/pack datasheet, protection design, charger IC,
thermistor tolerance, ADC error, aging limits, and abnormal-operation tests.
