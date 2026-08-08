# Simulator to FG23 Parameter Map

## Purpose

Keep Prototype 0 firmware tests aligned with the simulator scenarios. When board
measurements differ from assumptions, update the simulator inputs rather than
letting the two drift.

## Nominal Simulator Baseline

Source scenario:

```text
simulator/scenarios/six_nodes_nominal.yaml
```

| Simulator field | Baseline value | Firmware meaning |
|---|---:|---|
| `audio.frame_duration_ms` | 20 ms | Packet interval for synthetic audio frames. |
| `audio.encoded_bitrate_bps` | 24,000 bps | Synthetic payload rate. |
| `radio.bitrate_bps` | 500,000 bps | Target PHY bitrate or closest SDK profile. |
| `radio.overhead_bytes` | 16 bytes | Placeholder for measured radio/protocol overhead. |
| `radio.preamble_us` | 100 us | Placeholder for measured preamble/sync timing. |
| `schedule.slot_spacing_us` | 2500 us | Planned per-node TX opportunity spacing. |
| `radio.propagation_delay_us` | 2 us | Negligible bench placeholder. |

Derived baseline:

| Derived value | Value |
|---|---:|
| Synthetic payload bytes | 60 bytes |
| Simulated voice packet airtime | 1316 us |
| Simulated heartbeat airtime | 484 us |
| Slot guard | 1184 us |
| Six-node schedule span | 13,816 us |
| Planned channel utilization | 39.964% |

## Firmware Measurement Mapping

| Measurement | Updates simulator field |
|---|---|
| Actual useful PHY bitrate | `radio.bitrate_bps` |
| Measured packet airtime for 60-byte payload | `radio.overhead_bytes` and `radio.preamble_us` calibration |
| Measured scheduled TX launch error | slot guard assumption and future `schedule.guard_us` field |
| Measured RX/TX turnaround time | schedule feasibility assumptions |
| Measured packet loss in clean bench run | `radio.packet_loss_probability` baseline |
| Measured attenuation loss behavior | future scenario fault/loss windows |
| Measured current in TX/RX/idle | power budget docs |

## First Firmware Targets

E0-02 should start with:

- 20,000 us packet interval;
- 60-byte synthetic payload;
- closest available 500 kbps PHY profile;
- conservative TX power;
- one transmitter and one receiver;
- one-hour run.

E0-03 should start with:

- 20,000 us packet interval;
- 60-byte synthetic payload;
- 5,000 us scheduled-TX lead time;
- at least 100 scheduled transmission samples.

## Calibration Rule

If measured packet airtime differs materially from 1316 us, update the simulator
scenario or add a calibrated FG23 scenario before six-node expansion.
