# Startup and Operational Interlocks

**Document ID:** OR-ARC-017
**Revision:** 0.1
**Status:** Portable policy implemented; target integration pending

## Safety Invariant

Audio output begins muted and RF transmission begins prohibited. No target may
permit either merely because its main loop has started.

The ordered states are safe/off, rail stabilization, processor validation,
local readiness, and authenticated operation. Transition to local readiness
requires valid rails, authenticated firmware boot, valid configuration, safe
accessory state, and a healthy processor peer. Transition to operational state
additionally requires a valid authenticated crew session.

Loss of a crew session returns to muted local readiness and immediately removes
RF-transmit permission. Loss of a rail, boot, configuration, accessory, or peer
interlock enters a latched fault state with rails disabled by the requested
action mask. Unsafe pack input returns directly to the safe state. Rail and
processor startup waits are bounded; monotonic-clock rollback is a fault.

## Hardware Mapping

The target adapter maps actions from `openref_startup_supervisor` as follows:

- `ENABLE_RAILS` controls only the application load domains, never bypassing
  the always-on supervisor;
- `RELEASE_RESETS` releases both processor/codec reset sequencing only after
  rail-good qualification;
- `MUTE_AUDIO` uses the codec mute plus any independent amplifier shutdown;
- `PERMIT_RF_TX` gates the final transmit call as well as application intent;
- ready/fault actions drive bounded diagnostics and the user-status policy.

The hardware undervoltage/thermal cutoff remains authoritative even if
firmware requests enable. Firmware must default every mapped GPIO to the safer
state during reset and before pin mux configuration.

## Verification

Native tests cover ordering, crew-session gating, rail timeout, processor
timeout, pack loss, and time rollback. Target promotion additionally requires
power-on reset, brownout at each state transition, corrupt configuration,
invalid image, missing peer, accessory fault, session loss, and GPIO-reset-state
injection with physical observation of mute and RF-permit markers.
