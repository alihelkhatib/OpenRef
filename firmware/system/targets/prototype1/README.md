# Prototype 1 System Target

This directory is the integration boundary for the custom wearable system
controller. It deliberately contains no vendor startup project until the final
radio package/module and board support package are selected.

The first target implementation shall:

1. initialize all physical voice, playback, and radio gates disabled;
2. initialize the persistent settings runtime and report configuration validity;
3. sample power, accessory, peer, watchdog, update, service, and user state;
4. call `openref_system_runtime_tick()` from a monotonic control task;
5. implement gate callbacks that synchronously confirm the requested state;
6. keep the hardware watchdog unfed after a latched actuation failure;
7. record the failure and require a controlled reset to clear it.

Use `openref_watchdog_driver` as the only path to the target hardware-watchdog
feed operation. Register every communication-critical task with its portable
gate, report progress only after real forward work, and call the driver tick
from the monotonic control task. The driver configures the hardware watchdog
once, feeds only after all required tasks have made fresh progress, and latches
backend failure so a later callback recovery cannot resume feeding without a
controlled reset. Startup incompleteness, stale tasks, and clock rollback all
leave the hardware watchdog unfed.

Use `openref_update_stager` for radio and audio update writes. Target callbacks
must erase, program, and read the inactive slot; independently authenticate the
finished image; invalidate a rejected candidate; and transactionally persist
boot state. A callback must not alias the confirmed slot, silently skip
readback, or mark a slot pending before the final boot-state commit.

After a trial handoff, use `openref_boot_confirmation` with real clock, storage,
watchdog, critical-peripheral, peer-health, and authenticated-running-image
signals. The backend must transactionally persist the confirmed state; do not
confirm merely because application initialization returned successfully.

Back staging, trial-attempt, and confirmation persistence with
`openref_boot_state_store`. Map its two fixed 80-byte records to independent,
power-loss-safe NVM objects. Production runtime must load a valid record before
saving; the factory-only initializer is not a corruption-recovery shortcut.

The callback mapping must use the signal names and safe states in
`hardware/prototype1-wearable/electrical-interface-contract.json`. A successful
portable test is not evidence that a DMA channel, codec mute pin, or RF send
path stopped within its physical deadline; target promotion still requires
timing-marker capture and injected callback failures on hardware.
