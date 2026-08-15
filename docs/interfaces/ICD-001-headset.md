# OR-ICD-001: Headset Interface

**Revision:** 0.3
**Status:** Prototype electrical baseline; production connector deferred

## Purpose

Connect the wearable communication unit to an approved microphone and earpiece assembly.

## Required Behaviors

The interface shall:

- carry microphone input and listening audio;
- tolerate connection and disconnection while the unit is powered;
- prevent a connector fault from damaging the wearable unit;
- provide strain relief appropriate for running and collision-prone use;
- resist sweat and rain ingress in normal use;
- permit replacement of the headset as a wear item;
- support deterministic accessory compatibility;
- avoid user-accessible settings that can create unsafe listening levels.

## Deferred Decisions

- connector family;
- accessory identification;
- waterproofing approach.

## Prototype 1 Electrical Baseline

Prototype 1 uses a monaural analog headset with an electret microphone and one
earpiece. Keeping conversion inside the sealed wearable makes the headset a
passive, replaceable wear item and avoids putting an exposed digital bus in the
cable.

The custom electronics shall provide:

- current-limited, filtered microphone bias with open/short detection;
- AC-coupled differential or pseudo-differential microphone capture;
- input ESD protection and RF filtering at the connector boundary;
- a codec/headphone path rated for the approved minimum earpiece impedance;
- click/pop-controlled insertion, removal, mute, startup, and shutdown;
- a hardware output-gain ceiling that firmware cannot exceed;
- the block limiter and cumulative clipping diagnostics defined by the audio
  pipeline;
- the safe-boot, bounded-step, independent-mute, and no-rebound behavior defined
  by `OR-AUD-006`;
- series-impedance and measurement footprints for safe bring-up into a dummy
  load before human listening;
- an optional passive identification resistance, isolated from the audio path.

The exact microphone bias voltage/current, earpiece impedance, gain ceiling,
and connector pinout remain unset until representative headset candidates and
safe-output measurements exist.

## Accessory Fault Classification

The portable accessory monitor classifies connector disconnected, microphone
short, microphone open, sensor fault, and normal operation from a digital
connector indication plus microphone-bias sense voltage. Short-entry,
short-exit, open-exit, and open-entry thresholds are separately configured to
provide hysteresis. A configurable number of consecutive samples confirms a
reported state transition and prevents noisy boundary measurements from
chattering diagnostics or status.

Safety actions do not wait for state confirmation. Any raw disconnected,
open/short, or invalid measurement immediately mutes local transmission. A
disconnected connector or invalid sensing path also immediately requests
playback mute for pop/noise containment. Confirmed transitions are logged as
`OPENREF_EVENT_ACCESSORY_STATE` and feed the accessory alert in `OR-ICD-004`.

`firmware/system/common/openref_accessory_monitor.h/.c` implements this policy.
Thresholds and sampling interval must be derived from the selected bias circuit,
approved headset population, temperature range, wet contamination tests, and
ADC error budget; the example unit tests are not production calibration values.
