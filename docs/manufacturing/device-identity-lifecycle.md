# Device Identity Lifecycle

**Document ID:** OR-MFG-003
**Revision:** 0.2
**Status:** Portable policy and FG23 lifecycle persistence implemented; secure identity backend pending

## States and Allowed Direction

```text
BLANK -> FACTORY_TEST -> IDENTITY_INSTALLED -> PRODUCTION_LOCKED -> RETIRED
             |                 |                    |
             +-----------------+--------------------+-> QUARANTINED
```

Normal firmware provides no transition out of quarantined or retired states.
Rework of a quarantined unit requires an authenticated manufacturing procedure
that preserves the original failure record and explicitly determines whether
an installed identity must be revoked before replacement.

## Gates

- Factory test may begin only on a blank record.
- Identity generation requires all hardware tests passed and authenticated
  factory images. The backend generates the private identity internally;
  application firmware receives only an eight-byte public fingerprint.
- Production lock requires authenticated release images, verified authenticated
  boot, and successful application of the target debug-access policy.
- Any identity-generation, persistence, or debug-lock anomaly quarantines the
  unit in memory and prohibits a passing production result.
- Retirement requires explicit authorization, requests backend credential
  destruction, clears the application fingerprint, and remains retired even if
  the destruction callback reports failure. Such failure requires external
  revocation and controlled disposal.

Human-readable serials and public device IDs are not authentication secrets.
Private keys, session keys, provisioning blobs, and recovery secrets must never
enter the production result record or ordinary diagnostic logs.

## Persistence and Evidence

`firmware/system/common/openref_device_lifecycle.h/.c` implements transition
policy. The target backend must use protected, power-loss-safe storage and
verify irreversible debug and key operations. The production result schema is
version 2 and records the final lifecycle state plus the public fingerprint. A
`PASS` disposition requires `PRODUCTION_LOCKED`; provisioning anomalies require
both `QUARANTINE` disposition and `QUARANTINED` device state.

The lifecycle record has an explicit 36-byte little-endian serialization over a
CRC-protected, readback-verified dual-copy store. Semantic validation rejects
impossible combinations of state, generation, public ID, public fingerprint,
and failure code. Runtime writes require a successful prior load; blank factory
initialization is explicit. The FG23 backend uses isolated NVM3 keys `0x0f5230`
and `0x0f5231`. No private key or credential material enters this record.

Promotion requires duplicate-ID rejection at the manufacturing service,
power-loss injection at every transition, proof that private material is
non-exportable, debug-lock verification, retirement/revocation exercises, and
an audit linking every attempt without erasing earlier failures.
