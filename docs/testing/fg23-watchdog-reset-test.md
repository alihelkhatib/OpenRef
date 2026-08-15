# FG23 Watchdog Reset and Attribution Test

**Document ID:** OR-TST-012  
**Revision:** 0.1  
**Status:** Ready for bench execution

## Purpose

Verify AV-033/FW-004 on an FG23 development target by proving that loss of the
communication-critical application loop causes a hardware reset and that the
next boot attributes the reset to the watchdog rather than power, pin,
software, lockup, or brownout.

## Preconditions

- Use a non-reserved board; do not overwrite the COM12 external-timing image.
- Attach the 868 MHz antenna before powering any radio-capable image.
- Build with `-EnableNetwork -EnableHardwareWatchdog
  -WatchdogTestHangAfterFeeds 3 -WatchdogHangMarker PB3
  -WatchdogBootMarker PB2` and record the ELF/HEX hashes. Substitute only pins
  that are physically connected on the selected non-reserved board.
- Capture the diagnostic UART from before manual reset until at least one
  automatic reboot completes.
- For reset-time measurement, probe the hang and boot marker GPIOs with the
  logic analyzer. Serial ordering proves cause but
  is not precision timing evidence.

## Procedure

1. Flash the controlled test image to one non-reserved board and start a new
   serial capture without discarding the first boot records.
2. Reset the board once and confirm `openrefReset`, `openrefWatchdog Armed`, and
   `InjectedHang` records appear in that order.
3. Do not touch power or reset. Confirm the board automatically boots again.
4. Confirm the first `openrefReset` record after `InjectedHang` has a raw WDOG0
   or WDOG1 bit, the portable WATCHDOG bit, and `Watchdog:1`.
5. Validate the serial artifact:

   ```text
   python tools/validate_fg23_watchdog_reset.py CAPTURE.log --expected-feeds 3
   ```

6. Measure from the hang marker rising edge to the next boot-marker pulse.
   Record min/max over ten cycles,
   board serial, supply voltage, ambient temperature, firmware hashes, probe
   points, analyzer sample rate, and raw capture hash.

## Acceptance

- Ten of ten hangs cause automatic reset without operator action.
- Ten of ten subsequent boots are consistently attributed to WDOG0/WDOG1.
- No cycle is attributed only to power, pin, software, lockup, or brownout.
- No reset occurs before the injected hang.
- Preliminary engineering recovery is at most 2.0 seconds after the final feed.
  The production min/max limit remains blocked on measured watchdog-clock
  tolerance across voltage and temperature.
- The validator passes and the serial and logic-analyzer artifacts are retained
  by cryptographic hash.

Remove `-WatchdogTestHangAfterFeeds` after this test. A hang-injection build is
never a release candidate.
