# Prototype 0 Network Protocol

**Document ID:** OR-PRO-002  
**Revision:** 0.1  
**Status:** Three-board 80-byte LC3 payload passed; secured envelope simulated

## Purpose

Define the first executable OpenRef crew network. The implementation starts on
four FG23 development boards but reserves six deterministic voice slots so the
protocol can scale without changing its on-air format.

## Network Model

- A crew contains two through six nodes.
- Node IDs 1 through 6 are assigned during crew formation; ID 0 means broadcast.
- One node coordinates time and slot assignment but does not relay other nodes'
  voice traffic.
- Every audio frame is broadcast once in the source node's assigned slot.
- Crew identity and membership outlive the current coordinator.
- Coordinator loss starts a deterministic election; the lowest eligible active
  node wins in Prototype 0.

## Initial Schedule

The initial schedule is a 20 ms superframe with six 2.5 ms voice-slot starts.
The remaining 5 ms is reserved for control traffic, synchronization correction,
and engineering margin.

| Slot | Nominal start | Owner |
|---:|---:|---|
| 0 | 0.0 ms | Node 1 |
| 1 | 2.5 ms | Node 2 |
| 2 | 5.0 ms | Node 3 |
| 3 | 7.5 ms | Node 4 |
| 4 | 10.0 ms | Node 5, reserved on the four-board bench |
| 5 | 12.5 ms | Node 6, reserved on the four-board bench |

With the selected security envelope, the 80-byte encoded-audio payload becomes
96 bytes (8 counter bytes, 80 ciphertext bytes, and an 8-byte AES-CCM tag). The
complete 114-byte packet occupies about 1.924 ms at the current 500 kbit/s PHY,
including the modeled 100 us preamble. The provisional guard is therefore about
0.576 ms. E0-03 external
timing evidence must confirm or reduce that guard before the schedule is frozen.

## Version 1 Frame Header

The existing 18-byte little-endian Prototype 0 header remains authoritative:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 2 | Magic `0x4F52` |
| 2 | 1 | Version `1` |
| 3 | 1 | Kind: ping, audio, heartbeat, or control |
| 4 | 1 | Source node ID |
| 5 | 1 | Destination node ID; `0` is broadcast |
| 6 | 2 | Per-source sequence number |
| 8 | 8 | Source radio timestamp in microseconds |
| 16 | 2 | Payload length, 0 through 255 bytes |

Malformed magic, versions, kinds, lengths, and source ID zero are rejected before
the packet enters the crew state machine. The 18-byte header is authenticated as
AES-CCM additional data. The 96-byte secured payload envelope and 64-packet
replay window are specified in `OR-SEC-001`.

## Coordinator State

The coordinator broadcasts a heartbeat every 100 ms. A node considers the
coordinator absent after 300 ms without a valid heartbeat. Prototype 0 then waits
50 ms and selects the lowest eligible active node. Later revisions will add an
epoch and election priority so stale coordinators cannot reclaim the schedule.

## Four-Board Acceptance

The next bench image passes when:

1. COM8, COM10, COM12, and COM14 use one identical firmware image with fixed
   development node IDs.
2. All four broadcast one synthetic 20 ms audio frame in their assigned slots.
3. Each receiver reports independent per-source sequence, gap, late, duplicate,
   and RSSI counters.
4. A 10-minute run has no queue overflow, unexplained reset, or slot collision.
5. Removing the coordinator produces a replacement and resumed scheduling within
   500 ms.
6. Restoring the removed node does not create a second coordinator.

The two reserved slots are exercised in simulation until boards five and six are
available.

## Implementation Status

The vendor-independent state machine, fixed-length audio/heartbeat packet layer,
and FG23 scheduled RAIL adapter are implemented. A three-board live run on
2026-08-14 passed the final 80-byte LC3 payload size, coordinator replacement,
and rebooted-node rejoin with zero final-capture parse or scheduling failures.
COM12 remains on the E0-03 marker image until the external timing capture is
collected; four-board and ten-minute promotion tests remain pending.

The secured 114-byte wire-size model passes the deterministic six-node schedule
simulation with a 576 us slot guard. This is capacity evidence, not a live
encryption claim: FG23 crypto integration and E0-03 timing capture are pending.
