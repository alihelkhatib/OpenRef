# Packet-Pair Firmware Design

## Purpose

The packet-pair firmware is the first OpenRef-owned FG23 program after the
unmodified Silicon Labs example is proven.

It supports E0-02 Continuous Packet Pair and creates the measurement foundation
for scheduled transmission, capacity sweeps, and six-node scheduling.

## Modes

| Mode | Node role | Behavior |
|---|---|---|
| `packet_pair_tx` | Transmitter | Sends sequence-numbered packets at a fixed interval. |
| `packet_pair_rx` | Receiver | Receives packets, detects gaps, and logs metadata. |

Mode selection can initially be compile-time. Runtime mode selection may be
added after basic transport is stable.

## Initial Parameters

| Parameter | Initial value | Source |
|---|---:|---|
| Frequency | 915 MHz-class profile | Board/SDK-supported profile |
| Radio bitrate | 500,000 bps target | Simulator nominal baseline |
| Packet interval | 20,000 us | Simulator nominal frame interval |
| Payload bytes | 60 | 24 kbps encoded voice at 20 ms |
| Header bytes | SDK-dependent plus OpenRef header | Measure and record |
| TX power | Conservative bench value | Vendor profile |
| Run duration | 1 hour | E0-02 |

## Transmit State Machine

```text
BOOT
  -> RADIO_INIT
  -> IDLE_UNTIL_NEXT_PACKET
  -> BUILD_PACKET
  -> TX_QUEUE
  -> WAIT_TX_DONE
  -> IDLE_UNTIL_NEXT_PACKET
```

Required TX logs:

- `boot`
- `radio_init`
- `tx_queued`
- `tx_started` when the SDK exposes it or a GPIO marker can represent it
- `tx_done`
- `fault`

## Receive State Machine

```text
BOOT
  -> RADIO_INIT
  -> RX_START
  -> WAIT_RX
  -> PROCESS_RX
  -> RX_START
```

Required RX logs:

- `boot`
- `radio_init`
- `rx_done`
- `rx_gap`
- `fault`

## Packet Contents

Every packet starts with `openref_proto0_packet_header_t` from
`firmware/common/openref_proto0_packet.h`.

For E0-02:

- `kind`: `OPENREF_PROTO0_PACKET_PING`
- `source_id`: transmitter node ID
- `destination_id`: receiver node ID or 0 for broadcast
- `sequence`: incrementing 16-bit sequence
- `tx_timestamp_us`: local TX node timestamp at packet build time
- `payload_length`: synthetic payload byte count

The payload can initially be deterministic filler. Example pattern:

```text
payload[i] = (sequence + i) & 0xff
```

## Timing Rules

- Use monotonic local microsecond timestamps.
- Do not block inside radio callbacks.
- Copy callback results into a bounded event queue if the SDK requires callback
  context.
- Serial logging may lag radio events, but each log must include the event
  timestamp captured near the actual event.

## Exit Criteria

The packet-pair firmware is sufficient for E0-02 when:

- one TX and one RX node run for one hour;
- logs can be analyzed by `tools/analyze_packet_pair.py`;
- packet gaps, reset events, and fault events are visible;
- no unbounded queue or memory behavior is observed;
- RSSI/LQI/CRC metadata is recorded or unavailable fields are documented.

For final E0-02 evidence, run the analyzer with explicit criteria instead of
summary-only mode:

```powershell
python tools\analyze_packet_pair.py firmware\prototype0\fg23\results\YYYYMMDD-e0-02-packet-pair.csv --min-received 9000 --max-sequence-gaps 0 --max-rx-gap-events 0 --max-fault-events 0 --max-boot-events 1 --max-inter-arrival-us 100000 --json firmware\prototype0\fg23\results\YYYYMMDD-e0-02-summary.json
```

The analyzer writes `pass`, `criteria`, and `failures` when any criteria are
provided, and exits nonzero if the evidence does not meet the requested bounds.
