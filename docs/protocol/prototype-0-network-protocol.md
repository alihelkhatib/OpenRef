# Prototype 0 Network Protocol

**Document ID:** OR-PRO-002  
**Revision:** 0.2
**Status:** Three-board payload passed; portable security and admission implemented

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
50 ms and selects the lowest eligible active node.

Every authenticated heartbeat carries a 32-bit coordinator epoch and schedule
origin. A candidate must durably advance the epoch to a strictly greater value
before announcing itself coordinator. Persistence failure leaves the node in
election and produces `OPENREF_NETWORK_ACTION_EPOCH_FAILURE`; it does not permit
a volatile coordinator announcement. Epoch exhaustion also fails closed and
requires authenticated service recovery rather than wrapping to zero.

Receivers reject lower epochs. For competing authenticated coordinators at the
same epoch, the lower node ID wins deterministically; higher IDs are rejected.
This resolves equal-epoch observations while a formerly isolated coordinator
with an older epoch cannot reclaim the schedule after returning.

The default development configuration permits an in-memory increment so the
existing Prototype 0 overlay remains reproducible. Product configurations set
`require_persisted_epoch` and provide a power-loss-safe backend. The persisted
epoch belongs to the crew/session state and is distinct from the packet-nonce
boot counter.

The FG23 backend `openref_network_epoch_fg23` stores the epoch at NVM3 key
`0x0f5202`, distinct from boot-counter key `0x0f5201`. It loads the value before
network initialization, rejects mismatch with the caller's current epoch,
writes the increment, and verifies readback. The repository overlay enables it
with `-EnablePersistentEpoch`, which requires network mode. Enabled source
compiles against the installed Silicon Labs SDK; live power-cut evidence is
still required before promotion.

## Authenticated Crew Admission

A device accepts invitations only during a bounded window opened by a physical
join action. It generates a fresh 32-byte challenge using the target secure RNG.
The coordinator returns one fixed 168-byte invitation; bytes 0 through 103 are
the signed region.

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | Magic `ORJN` |
| 4 | 1 | Admission version `1` |
| 5 | 1 | Assigned local node ID, 1 through 6 |
| 6 | 1 | Complete six-bit member mask |
| 7 | 1 | Member count, 2 through 6 |
| 8 | 4 | Nonzero crew session ID |
| 12 | 4 | Strictly increasing per-device admission counter |
| 16 | 32 | Device challenge |
| 48 | 8 | Trusted coordinator public-identity fingerprint |
| 56 | 16 | Roster/transcript digest |
| 72 | 32 | Session key wrapped specifically for this device/transcript |
| 104 | 64 | Coordinator signature over bytes 0 through 103 |

The receiver validates field consistency, its challenge, coordinator identity,
signature, and replay counter before unwrapping. It durably advances the counter
before installing the 128-bit crew key through `openref_crew_session`; a failed
install consumes the invitation rather than allowing replay. Raw keys and
challenges are wiped after use. Wrong, expired, malformed, untrusted, replayed,
or unwrap-failed invitations close the window and contribute to bounded lockout.

The invitation fits existing control-packet payload capacity but does not share
the voice security envelope because the crew key does not exist yet. Target
cryptography must bind the wrapped key to the intended device identity and the
entire signed transcript. The approved signature and wrapping/KEM algorithms,
coordinator trust establishment, and multi-device formation UX require security
review and live validation.

On FG23, the invitation replay counter uses verified NVM3 domain key
`0x0f5203`. `openref_security_counter_fg23_load` initializes the portable
admission state, and `openref_security_counter_fg23_persist` is the persist
callback with an admission-domain context. The same adapter exposes a distinct
service domain; the complete target object map is `OR-ARC-019`.

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

The vendor-independent state machine, epoch-bearing heartbeat packet layer,
and FG23 scheduled RAIL adapter are implemented. A three-board live run on
2026-08-14 passed the final 80-byte LC3 payload size, coordinator replacement,
and rebooted-node rejoin with zero final-capture parse or scheduling failures.
COM12 remains on the E0-03 marker image until the external timing capture is
collected; four-board and ten-minute promotion tests remain pending.

The secured 114-byte wire-size model passes the deterministic six-node schedule
simulation with a 576 us slot guard. This is capacity evidence, not a live
encryption claim: FG23 crypto integration and E0-03 timing capture are pending.
