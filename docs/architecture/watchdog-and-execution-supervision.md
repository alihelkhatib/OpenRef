# Watchdog and Execution Supervision

**Document ID:** OR-ARC-016
**Revision:** 0.1
**Status:** Portable policy implemented; target integration pending

## Purpose

Prevent a partially running scheduler from continuously feeding a hardware
watchdog while a communication-critical task is deadlocked, starved, or no
longer meeting its bounded execution obligation.

## Policy

Each processor configures a bit for every critical execution path and a maximum
progress age for that path. A task reports progress only after completing its
meaningful unit of work; merely entering a timer callback or idle loop is not
progress. The central watchdog task services the hardware watchdog only when:

1. every required task has reported since the previous feed;
2. every task's most recent report is within its configured timeout;
3. the monotonic time source has not moved backward.

After a feed, all progress bits are consumed. Repeated calls by the watchdog
task cannot substitute for fresh task execution. Missing tasks are tolerated
only during the bounded startup grace interval, and the watchdog is not fed
during that grace until all required tasks actually report.

## Initial Task Allocation

| Processor | Required progress source | Meaningful completion point |
|---|---|---|
| FG23 | radio event service | RAIL event queue drained to its bounded limit |
| FG23 | network/schedule service | current slot decision completed |
| FG23 | secure packet service | pending packet admitted/rejected without backlog growth |
| FG23 | audio-link service | requested SPI transaction completed or explicitly idle |
| RT595 | capture service | next 10 ms PCM block committed |
| RT595 | codec/render service | encode plus due playout render completed |
| RT595 | audio-link service | SPI queues serviced without blocking the audio deadline |
| RT595 | control/power service | controls, peer heartbeat, and safety inputs sampled |

Final timeout values must exceed verified worst-case scheduling jitter while
remaining below the configured hardware watchdog period. They are measured
inputs, not arbitrary constants.

## Fault and Reset Behavior

On the first unhealthy evaluation, record `OPENREF_EVENT_WATCHDOG_WITHHELD`
with the task fault mask, processor source, and fatal severity. Do not perform
unbounded logging, flash erasure, network transmission, or peer recovery in the
watchdog path. Mute output through an independent safe path where possible,
then allow the hardware watchdog to reset the local processor.

Reset-reason handling records watchdog reset early in the next boot. Repeated
watchdog resets enter the authenticated recovery/fallback policy rather than a
permanent rapid-reset loop. The peer supervisor may reset the other processor
after heartbeat loss, but it must not feed or disable that processor's local
watchdog.

## Implementation and Promotion Evidence

`firmware/system/common/openref_watchdog_gate.h/.c` implements the portable
multi-task gate. Each target must provide a monotonic clock, hardware watchdog
configuration, early reset-reason capture, safe mute, and diagnostic adapter.

Promotion requires injected hangs in every registered task, priority-starvation
tests, timer wrap/rollback tests, boot-loop recovery, and proof that the maximum
healthy interval between hardware feeds remains inside the watchdog window.
