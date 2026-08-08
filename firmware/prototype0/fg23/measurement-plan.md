# FG23 Prototype 0 Measurement Plan

## Measurement Priorities

1. Packet transport stability.
2. Scheduled TX timing error.
3. Useful payload throughput.
4. Current draw in TX, RX, idle, and continuous packet modes.
5. RF behavior under attenuation or shielding.

## Serial Log Files

Store local raw captures under:

```text
firmware/prototype0/fg23/results/
```

Generated logs are ignored by Git. Commit only concise summaries and any
scripts needed to reproduce analysis.

## Required Metrics

For packet-pair runs:

- sent packet count;
- received packet count;
- delivery ratio;
- sequence gaps;
- CRC failures where exposed by SDK;
- reset count;
- inter-arrival min, mean, p95, p99, max;
- RSSI/LQI min, mean, p95, p99 where available.

For scheduled TX:

- requested TX timestamp;
- accepted/rejected result;
- observed GPIO TX start time;
- launch error min, mean, p95, p99, max.

For current measurements:

- board role;
- PHY/profile;
- packet interval;
- payload length;
- measured voltage;
- mean current;
- peak current if available;
- measurement tool and sampling method.

For audio loopback:

- impulse or digital marker timestamp;
- capture-frame timestamp;
- packet-queue timestamp;
- TX-start timestamp;
- RX-done timestamp;
- playback-output timestamp;
- capture, queue, radio, playback, and end-to-end latency min, mean, p95,
  p99, and max.

## Result Naming

Use stable names:

```text
YYYYMMDD-e0-01-toolchain.md
YYYYMMDD-e0-02-packet-pair.csv
YYYYMMDD-e0-03-scheduled-tx.csv
YYYYMMDD-e0-07-audio-loopback.csv
YYYYMMDD-current-profile.csv
```

## First Bench Configuration

- Keep boards separated by at least 1 m.
- Start at conservative TX power.
- Use vendor antennas included with the kit.
- Avoid human listening tests until audio output limits are verified.
- Keep one board fixed as transmitter and one as receiver for the first run.
