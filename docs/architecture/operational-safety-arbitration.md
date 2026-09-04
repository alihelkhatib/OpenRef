# Operational Safety Arbitration

**Document ID:** OR-ARC-018
**Revision:** 0.1
**Status:** Portable policy and fail-closed target output gate implemented;
hardware callbacks and physical timing evidence pending

## Purpose

Subsystems may request mute or transmission inhibition independently. No
subsystem callback may directly clear another subsystem's request. The final
voice-uplink, playback, and network-control enables are therefore produced by a
single stateless fail-closed arbitration step each control cycle.

## Inhibit sources

The arbiter retains independent reason bits for power, startup, accessory,
processor peer, local watchdog, update, privileged service, user request, and
unclassified system fault. Outputs are enabled only when every applicable
reason is absent.

| Source | Voice uplink | Playback | Network/control RF |
|---|---:|---:|---:|
| Power mute/shutdown | inhibit | inhibit | inhibit |
| Startup mute/no RF permit | inhibit | inhibit | inhibit as requested |
| Accessory fault | inhibit as requested | inhibit as requested | permit |
| Audio-peer recovery/fault | inhibit | inhibit | permit |
| Local watchdog unhealthy | inhibit | inhibit | inhibit |
| Update active | inhibit | inhibit | inhibit |
| Privileged service active | inhibit | inhibit | inhibit |
| User transmit/listening mute | independently inhibit | independently inhibit | permit |
| Unclassified system fault | inhibit | inhibit | inhibit |

Allowing network/control RF during an isolated accessory or audio-processor
fault lets a healthy radio report degradation and remain recoverable. It does
not send captured voice because voice uplink has its own stricter gate.

## Target integration

`firmware/system/common/openref_safety_arbiter.h/.c` accepts action outputs from
the power, startup, accessory, peer, watchdog, update/service, and user-control
policies. The target maps playback reasons into independent
`openref_volume_manager` mute reasons and maps transmit reasons before LC3
capture is admitted to the radio queue. Every radio send path checks the final
network-control gate, and every voice packet path additionally checks the voice
gate. DMA already in flight is replaced by silence or invalid codec flags when
the gate closes; stale audio is never released after reopening.

Because the arbiter is combinational, clearing one input cannot clear any other
reason. A null or missing input produces all outputs disabled. Target promotion
requires GPIO/trace observation while independently injecting every source,
simultaneous faults, fault clearing in every order, and callback races at audio
and radio deadline boundaries.

`openref_safety_output_gate` applies the arbiter result to target callbacks. It
starts with all outputs disabled, removes permissions before adding any, enables
network/control transport before playback and captured voice, and latches safe
after any callback failure. A target callback must synchronously confirm that
the requested hardware or queue gate took effect; deferred requests are not a
successful application.
