# Diagnostics and Service Data

**Document ID:** OR-ARC-014
**Revision:** 0.2
**Status:** Portable volatile event log implemented

OpenRef records bounded operational events needed to reproduce failures without
recording voice content, packet payloads, session keys, nonces, headset audio,
or user-entered secrets. The implementation is
`firmware/system/common/openref_diagnostics.h/.c`.

## Record format

Each explicit 16-byte little-endian record contains:

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 8 | Monotonic timestamp in milliseconds |
| 8 | 4 | Event-specific numeric value |
| 12 | 2 | Stable event code |
| 14 | 1 | Source node or processor identifier |
| 15 | 1 | Severity |

The initial volatile ring contains 32 records and overwrites the oldest record
when full. Recorded and overwritten totals remain observable. Explicit encoding
is used for export; the in-memory C structure is never treated as a wire format.

## Event coverage

The initial registry covers boot, join and coordinator changes, authentication
and replay rejection, audio deadline/capture/queue faults, battery warnings and
shutdowns, overtemperature, peer reset/power-cycle/failure, and assertions.

## Privacy and retention rules

- Event values are counters, durations, state identifiers, or bounded sensor
  readings only.
- Voice, encoded audio, packet bodies, keys, and stable user identity are
  prohibited from diagnostic records.
- Volatile logging is the baseline. Persistent crash retention requires a
  separately bounded, wear-aware store and an explicit retention policy.
- Export requires physical maintenance access or authenticated service mode.
- Factory reset erases persistent service records and credentials.

Authenticated service mode is defined by `OR-ICD-010`. Diagnostic export uses
only the diagnostic permission and does not inherit configuration, update,
factory, or identity authority. Session expiry, disconnect, clock fault, or
explicit exit immediately removes export permission.

## Promotion tests

Fault-injection runs must verify event codes, ordering, timestamp monotonicity,
ring overwrite behavior, reset survival policy, export authorization, and
absence of sensitive buffers in exported data.
