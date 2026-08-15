# Persistent Configuration Store

**Document ID:** OR-ICD-009
**Revision:** 0.2
**Status:** Version 1 schema and portable contract implemented; physical target validation pending

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
record policy.

## Version 1 Payload

Schema version 1 has an exact payload length of 16 bytes. The encoding is
defined by `openref_settings_v1.h/.c`; it does not depend on compiler structure
layout.

| Payload offset | Bytes | Field | Acceptance rule |
|---:|---:|---|---|
| 0 | 1 | Preferred listening-volume step | Less than the active calibrated table's step count |
| 1 | 1 | Accessory profile ID | Nonzero member of the firmware-approved accessory table |
| 2 | 1 | Indicator profile ID | Nonzero member of the firmware-approved indication table |
| 3 | 1 | Regulatory-region ID | Exact match for the compiled and authorized product region |
| 4 | 4 | Calibration revision | Exact match for the active approved calibration set |
| 8 | 4 | Policy revision | Exact match for the active approved policy set |
| 12 | 4 | Reserved | All zero |

The preferred volume is a request, not authority to energize audio. Startup
mute and every safety inhibit remain active while it is restored, and the
request is accepted only against the active calibrated volume table. Profile
IDs select complete firmware-approved tables; the record cannot inject raw
thresholds, gain values, or timing parameters.

The following are deliberately excluded: credentials and keys; crew, session,
or device identity; boot, epoch, admission, service, and replay counters;
firmware-slot metadata; safety thresholds and gain tables; raw calibration;
and diagnostics. These use dedicated protected stores or compiled controlled
data.

An unknown schema, wrong payload length, nonzero reserved byte, unavailable
profile, region mismatch, or calibration/policy revision mismatch rejects the
record. Firmware must use controlled defaults or require reprovisioning; it
must not reinterpret incompatible bytes. A future schema requires an explicit,
tested migration routine that first validates the complete source record and
writes a new generation without destroying the last valid copy.

`openref_settings_runtime.h/.c` joins the record store, v1 decoder, controlled
defaults, and volume manager. A missing or corrupt record selects defaults. A
valid persisted preferred step is clamped to the live volume ceiling, and
restoration never clears startup or fault mute bits. The Prototype 0 FG23
application is a radio harness and does not contain the product audio/startup
graph; this runtime is integrated at the Prototype 1 system target instead of
manufacturing false product-level evidence in the radio harness.

The FG23 target adapter uses separate NVM3 objects `0x0f5210` and `0x0f5211`,
requires exact data-object type and 80-byte length, and exposes the standard
portable read/write callbacks. It is enabled by the repository overlay switch
`-EnablePersistentConfig`. Enabled source compiles against the installed SDK;
migration to any future schema, endurance characterization, and physical
brownout testing are still required.
