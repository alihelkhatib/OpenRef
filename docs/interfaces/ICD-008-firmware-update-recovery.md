# Firmware Update and Recovery Interface

**Document ID:** OR-ICD-008
**Revision:** 0.2
**Status:** Portable manifest and boot policies implemented; platform bootloaders pending

## Ownership

Each processor owns its flash writes, image authentication, boot handoff, and
watchdog. The radio processor coordinates user-visible maintenance state but
cannot instruct either bootloader to execute an unauthenticated image.

## Slot policy

The portable policy in `firmware/system/common/openref_boot_policy.h/.c` assumes
two independently verifiable slots. Platform code supplies, for each slot,
presence, authenticated status, and authenticated monotonic version.

- Only present, authenticated images at or above the stored version floor are
  eligible.
- An update is staged only in the non-confirmed slot.
- Trial-attempt state is persisted before every trial handoff.
- An unconfirmed image receives a bounded number of boot attempts.
- Exhausted, missing, or invalid pending images fall back to the confirmed slot.
- Confirmation clears pending state and advances the anti-rollback floor.
- If the confirmed slot is invalid, another authenticated slot at the version
  floor may enter restricted recovery mode.
- If no eligible slot exists, the bootloader remains in authenticated recovery;
  it must not jump to an unverified address.

## Transactional state

Boot state is a versioned, CRC-protected, dual-copy or platform-transactional
record containing confirmed slot, pending slot, trial attempts, and minimum
version. Selection returns whether the record changed; the bootloader must
durably commit that change before jumping. Failure to commit a trial-attempt
increment makes the candidate ineligible for that boot, preventing a reset loop
from bypassing the attempt limit.

`openref_boot_state_store` provides the portable dual-copy implementation over
two target records. It serializes the state explicitly rather than persisting C
structure padding, validates CRC/schema/generation through `openref_config_store`,
then validates slot and pending-attempt semantics. Writes target the inactive
record and become current only after exact readback. Runtime saves require a
successful prior load; only an explicit factory-initialize call may create the
first generation. Corrupt new writes retain the previous generation, generation
exhaustion never wraps, and semantically invalid records fail closed.

## Confirmation

An application confirms itself only after clocks, persistent storage, watchdog,
critical peripherals, and its peer-health interface have remained healthy for a
defined soak interval. Merely reaching `main()` is insufficient. Radio and audio
images are independently confirmed so one failed processor does not invalidate
the other's working image.

`openref_boot_confirmation` implements this continuous-health gate for a trial
image. It accepts only the authenticated pending slot, requires every health
input continuously for the configured soak, and restarts the full interval on
any unhealthy sample or monotonic-clock rollback. Confirmation and
anti-rollback-floor advancement are applied to a copy and become active only
after the target persists that copy. Persistence failure latches the gate and
leaves the original confirmed slot and floor unchanged until reset.

## Security

The signed manifest binds processor target, hardware compatibility, image size,
cryptographic digest, version, and release identity. Update transport may be
untrusted because activation depends on local signature verification. Signing
keys are not stored in the repository, fixture logs, or ordinary application
storage.

### Fixed manifest version 1

The signed manifest is exactly 144 bytes. Integers are little-endian and bytes
0 through 79 are the signed region.

| Offset | Bytes | Field |
|---:|---:|---|
| 0 | 4 | Magic `ORUP` |
| 4 | 1 | Manifest format, `1` |
| 5 | 1 | Processor target: radio `1`, audio `2` |
| 6 | 2 | Reserved, zero |
| 8 | 4 | Exact hardware compatibility ID |
| 12 | 4 | Monotonic image version |
| 16 | 4 | Minimum bootloader version |
| 20 | 4 | Exact image size |
| 24 | 32 | SHA-256 image digest |
| 56 | 16 | Nonzero release identity |
| 72 | 8 | Trusted signing-key identifier |
| 80 | 64 | Signature over bytes 0 through 79 |

`openref_update_verifier` rejects wrong target/hardware, non-newer or rollback
versions, unsupported bootloader requirements, zero/oversized images, empty
identity fields, reserved-bit use, and invalid signatures before accepting image
data. It hashes bounded image chunks through a platform SHA-256 callback,
rejects overflow or truncation, and compares the completed digest in constant
time. A verified result only authorizes staging to the inactive slot; activation
still follows the transactional boot policy and cannot overwrite the confirmed
recovery image.

The target signature adapter fixes the approved algorithm and trusted key set;
key identifiers do not permit arbitrary caller-supplied public keys. Manifest
and image failures record `OPENREF_EVENT_UPDATE_REJECTED` without logging image
contents or signature material.

`openref_update_stager` binds this verifier to a target flash backend. It derives
the candidate as the slot opposite the confirmed image, erases only after the
manifest passes, limits streamed chunks to 256 bytes, reads back and compares
every write, completes the image digest, requests independent target slot
authentication, and persists pending boot state last. Any erase/write/readback,
digest, authentication, or boot-state persistence failure invalidates the
candidate and latches the staging transaction until reinitialization. The
in-memory boot state is not advanced when its durable commit fails.

## Verification

Tests must remove power during erase, write, manifest commit, trial-count commit,
first boot, and confirmation. They must also cover wrong target, truncated image,
invalid signature, bit corruption, version rollback, repeated watchdog reset,
both slots invalid, and successful fallback without erasing identity.
