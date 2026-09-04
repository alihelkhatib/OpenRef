# Persistent Configuration Store

**Document ID:** OR-ICD-009
**Revision:** 0.1
**Status:** Portable contract implemented; target backend pending

## Scope

The configuration store preserves non-secret user and unit settings across
reset, brownout, and battery replacement. Cryptographic keys, boot counters,
firmware-slot metadata, and high-rate diagnostics use their own protected
stores and must not be placed in this record.

## Record Contract

Two independent backend slots each hold an 80-byte record. Multi-byte fields
are little-endian.

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | Magic `0x4346524F` (`ORFC` on wire) |
| 4 | 2 | Nonzero schema version |
| 6 | 2 | Payload length, 1 through 64 |
| 8 | 4 | Nonzero generation |
| 12 | 64 | Payload and zero padding |
| 76 | 4 | CRC-32 over bytes 0 through 75 |

On load, both slots are independently validated and the newer valid generation
is selected using serial-number arithmetic. A corrupt or interrupted newest
record therefore falls back to the prior valid record. A schema or payload-size
mismatch is not silently interpreted.

On save, firmware writes the inactive slot, reads the complete record back,
validates its CRC and metadata, and compares every byte before changing active
state. Generation exhaustion fails closed. The platform backend must guarantee
that a torn write cannot corrupt the other slot and must document its flash
erase granularity and endurance.

`firmware/system/common/openref_config_store.h/.c` implements the portable
policy. Target adapters, concrete schema fields, migration tooling, and
brownout fault-injection evidence remain open.
