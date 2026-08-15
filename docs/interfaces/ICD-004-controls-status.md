# OR-ICD-004: Controls and Status

**Revision:** 0.2
**Status:** Semantic firmware baseline; physical interaction pending

## Controls

Core functions shall be operable with wet hands and gloves without menu navigation.

Candidate control functions:

- power;
- listening volume;
- mute or privacy control, if retained;
- crew formation or join action;
- service or recovery action protected from accidental activation.

The portable input boundary supports four independent active-state buttons,
configurable debounce and configurable protected long-press timing. It emits
edge events only after a stable interval and emits each long press once per
physical hold. Timer rollback emits no user action and is counted as a clock
fault. Targets convert electrically active-low inputs to the logical pressed
mask before this boundary. Exact timing values are promoted only after wet-hand,
glove, motion, and accidental-activation testing.

`firmware/system/common/openref_button_filter.h/.c` implements this filtering;
mapping a press or long press to power, join, recovery, or service authority is
a separate interaction-policy decision.

## Status

The system shall communicate at least:

- powered and ready;
- forming or joining a crew;
- connected;
- degraded communication;
- low and critical battery;
- charging;
- fault;
- update or recovery mode.

Exact colors, tones, vibration patterns, and button timing remain deferred until the interaction model is validated.

## Semantic Status Contract

The portable policy exposes one mutually exclusive base mode and independent
alert flags. Base modes are off, booting, forming, connected, charging,
update/recovery, and fault. Alerts are low battery, critical battery, degraded
link, and accessory fault. This separation prevents a connected indication from
hiding a battery or link warning.

Operational readiness is true only when the base mode is connected and there is
no critical-battery, degraded-link, or accessory alert. Low battery remains an
explicit warning but does not by itself claim the unit is unusable. Fault and
update/recovery modes take priority over ordinary network activity.

Critical-battery, degraded-link, and fault transitions emit one-shot attention
events suitable for a validated vibration or tone pattern. Holding a condition
does not repeatedly retrigger attention on every firmware cycle. Contradictory
inputs, including simultaneous forming and connected states or critical battery
without low battery, produce a visible fault rather than a misleading ready
indication.

`firmware/system/common/openref_status_policy.h/.c` implements these semantics.
LED colors, flash timing, vibration patterns, acknowledgment behavior, ambient
visibility, color-vision accessibility, and wet/glove usability remain physical
human-factors validation inputs.
