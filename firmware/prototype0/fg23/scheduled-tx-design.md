# Scheduled TX Design

## Purpose

E0-03 measures whether the FG23 radio stack can accept transmissions scheduled
against local radio/system time and launch them with bounded error.

This is the key evidence needed before six-node time-slot scheduling.

## Test Concept

One node repeatedly schedules packets for future transmission. GPIO markers and
serial logs capture the difference between:

- requested TX timestamp;
- SDK acceptance time;
- observed TX start marker;
- TX completion marker.

## Initial Parameters

| Parameter | Initial value |
|---|---:|
| Packet interval | 20,000 us |
| Lead time before TX | 5,000 us |
| Payload bytes | 60 |
| Sample count | 100 minimum |
| Radio bitrate | 500,000 bps target |

## Required GPIO Markers

| Marker | Meaning |
|---|---|
| `pkt_build` | Packet header and payload finished. |
| `tx_queue` | Scheduled TX submitted to radio API. |
| `tx_start` | Transmission start observed or best SDK-supported proxy. |
| `tx_done` | Transmission completion observed. |

If the SDK cannot expose true TX start, document the closest available signal.

## Required Logs

Add or extend these serial events:

```text
tx_queued detail=requested_tx_us=<value> lead_time_us=<value> length=<value>
tx_started detail=requested_tx_us=<value> launch_error_us=<value>
tx_done detail=airtime_us=<value>
fault detail=sdk_result=<value>
```

## Pass Criteria

E0-03 passes when:

- at least 100 scheduled transmissions are attempted;
- acceptance/rejection result is logged for each attempt;
- GPIO or SDK timing marker is captured;
- launch error min, mean, p95, p99, and max can be computed;
- no unexplained reset occurs;
- timing jitter is small enough to support a six-node schedule with guard time.

The first simulator baseline has 1184 us slot guard for 20 ms, 24 kbps,
500 kbps radio, 2500 us slot spacing. Measured launch error must leave enough
remaining guard for clock drift, RX/TX turnaround, and implementation overhead.
