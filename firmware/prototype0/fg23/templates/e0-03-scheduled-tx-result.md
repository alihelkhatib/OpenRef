# E0-03 Scheduled Transmission Result

**Date:** TBD  
**Tester:** TBD  
**Status:** Draft

## Configuration

| Item | Value |
|---|---|
| Firmware build ID | TBD |
| Node ID | TBD |
| Frequency | TBD |
| Radio bitrate | TBD |
| TX power | TBD |
| Payload length | TBD |
| Packet interval | TBD |
| Scheduled TX lead time | TBD |
| Sample count | TBD |
| Measurement instrument | TBD |

## Raw Evidence

- Serial log: TBD
- Logic analyzer capture: TBD
- Oscilloscope capture: TBD
- Timing export CSV: TBD

## Timing Summary

| Metric | Value |
|---|---:|
| Scheduled attempts | TBD |
| Accepted attempts | TBD |
| Rejected attempts | TBD |
| Launch error min us | TBD |
| Launch error mean us | TBD |
| Launch error p95 us | TBD |
| Launch error p99 us | TBD |
| Launch error max us | TBD |
| TX duration mean us | TBD |

## Pass/Fail Criteria

- [ ] At least 100 scheduled transmissions attempted.
- [ ] Acceptance/rejection logged for each attempt.
- [ ] Timing marker captured.
- [ ] Launch error distribution computed.
- [ ] No unexplained reset.
- [ ] Launch error is compatible with simulator slot guard.

## Deviations

TBD

## Decision

- [ ] Proceed to E0-04 payload capacity sweep.
- [ ] Repeat E0-03.
- [ ] Blocked pending corrective action.
