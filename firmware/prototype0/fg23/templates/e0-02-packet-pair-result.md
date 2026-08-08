# E0-02 Continuous Packet Pair Result

**Date:** TBD  
**Tester:** TBD  
**Status:** Draft

## Configuration

| Item | Value |
|---|---|
| Firmware build ID | TBD |
| TX node ID | TBD |
| RX node ID | TBD |
| Frequency | TBD |
| Radio bitrate | TBD |
| TX power | TBD |
| Payload length | TBD |
| Packet interval | TBD |
| Run duration | TBD |
| Board separation | TBD |

## Raw Evidence

- TX serial log: TBD
- RX serial log: TBD
- Analyzer JSON: TBD
- Current measurement file: TBD

## Analyzer Summary

Paste `tools/analyze_packet_pair.py` summary here.

```json
{}
```

## Pass/Fail Criteria

- [ ] One-hour run completed.
- [ ] No unexplained board reset.
- [ ] Received packet count recorded.
- [ ] Sequence gaps recorded.
- [ ] Inter-arrival min, mean, p95, p99, and max recorded.
- [ ] RSSI/LQI recorded or unavailability explained.
- [ ] Result is good enough to proceed to E0-03 scheduled TX.

## Deviations

TBD

## Decision

- [ ] Proceed to E0-03.
- [ ] Repeat E0-02.
- [ ] Blocked pending corrective action.
