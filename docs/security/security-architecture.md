# Security Architecture

**Document ID:** OR-SEC-001  
**Revision:** 0.4
**Status:** Prototype 0 packet protection specified; hardware integration pending

## Security Goals

OpenRef shall protect:

- crew membership;
- live voice confidentiality;
- voice and control integrity;
- device identity;
- firmware authenticity;
- recovery from lost or compromised units;
- manufacturing credentials.

## Trust Boundaries

Trust boundaries exist between:

- manufacturing systems and device;
- bootloader and application;
- device and crew network;
- field user and maintenance interface;
- diagnostic logs and exported tools;
- firmware release system and update package.

## Device Identity

Each production unit shall have:

- a unique device identifier;
- a unique cryptographic identity;
- protected key storage appropriate to the selected hardware;
- a revocation or retirement mechanism.

Human-readable serial numbers shall not serve as security credentials.

## Crew Formation

Crew setup shall establish:

- a unique crew session;
- authenticated membership;
- fresh session keys;
- protection against replay;
- explicit indication of successful or failed admission.

The product shall avoid requiring users to manually enter long secrets during normal match setup.

The portable `openref_crew_admission` protocol binds physical join intent, a
fresh device challenge, dynamic node assignment, complete member mask, crew
session identity, persistent anti-replay counter, coordinator identity,
roster/transcript digest, and device-specific wrapped key into a signed
invitation. The counter is durably advanced before activation. The
`openref_crew_session` boundary then validates membership, installs the 128-bit
session key through an opaque secure-key backend, and wipes the caller's key
buffer. Application state retains membership and session metadata, not the raw
key. Leaving a crew erases the backend key and disables the session even if
backend erasure reports a failure. Algorithm selection, coordinator trust,
multi-device formation UX, and FG23 identity/key backends remain promotion
gates.

## Voice and Control Protection

- voice packets shall be authenticated and encrypted;
- control traffic shall be authenticated;
- sequence or freshness information shall prevent replay;
- malformed traffic shall be rejected before expensive processing where possible;
- repeated authentication failures shall be rate limited and logged.

### Prototype 0 authenticated envelope

Prototype 0 uses AES-CCM with a 128-bit crew-session key and an 8-byte tag. The
existing 18-byte network header remains visible and is supplied to AES-CCM as
additional authenticated data. The protected payload is:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | Monotonic boot counter, little-endian |
| 4 | 4 | Per-boot packet counter, little-endian |
| 8 | 80 | Encrypted payload |
| 88 | 8 | AES-CCM authentication tag |

The 13-byte nonce is `crew_session_id[4] || source_id[1] || boot_counter[4] ||
packet_counter[4]`, with multibyte values little-endian. A device must persist a
strictly increasing boot counter before transmitting and must never wrap its
packet counter under the same boot counter and session key. Failure to advance
the persistent boot counter disables protected transmission until recovery or
reprovisioning; nonce reuse is not permitted.

Receivers authenticate before altering replay state. Each source has a
64-packet sliding replay window for the current boot counter. Duplicate, stale,
or older-boot packets are rejected. A newer authenticated boot counter resets
that source's replay window.

The Python AES-CCM implementation is a deterministic reference and test-vector
generator. The portable C layer implements envelope construction/opening,
nonce construction, and post-authentication replay admission through a narrow
CCM callback contract. The Silicon Labs SE Manager backend, protected
boot-counter storage, key provisioning, and live encrypted radio test remain
open.

## Firmware Security

`openref_secure_transport.h/.c` owns the per-boot transmit counter, six replay
windows, exhaustion, and failure accounting. The optional FG23 network path
uses 114-byte secured frames and authenticates each frame before parsing or
schedule-state changes. It refuses radio startup until runtime crew-session
provisioning supplies a key, session ID, advanced persistent boot counter, and
packet-counter start. Target syntax is verified against the installed FG23 SDK
and SE Manager headers; live promotion and final project-component linkage
remain target work.

`openref_secure_startup` advances and verifies the boot counter before exposing
the crew-session key backend. Successful admission then provisions the radio
with that exact boot counter and packet counter 1; leaving the crew aborts RAIL
activity before volatile transport and SE key context are wiped. Counter
failure clears the startup object, so a stale backend cannot survive an
exhausted or unreadable counter. The FG23 adapter joins these operations without
duplicating portable counter policy.

The portable implementation includes fixed envelope wrapping/opening and only
changes replay state after the platform CCM callback succeeds. FG23 adapters
use Silicon Labs SE Manager for AES-CCM and NVM3 for the boot counter. Startup
writes, reads back, and verifies the increment; backend failure, corruption, or
counter exhaustion fails closed. No fallback session key is embedded.

- firmware images shall be signed;
- the boot chain shall verify authenticity before execution;
- interrupted updates shall preserve a recoverable image;
- rollback policy shall be explicit;
- debug interfaces shall be controlled in production units.

## Manufacturing Provisioning

Provisioning shall:

- create or inject per-device credentials;
- avoid shared fleet-wide private secrets;
- produce an auditable result;
- support failed-unit quarantine;
- prevent credentials from appearing in ordinary production logs.

The controlled lifecycle and public manufacturing evidence are specified by
`OR-MFG-003`. The portable transition policy never transports a private key:
the secure backend generates identity material internally and returns only a
public fingerprint. Production lock, quarantine, retirement, and backend
failure behavior are executable; secure-element provisioning, fleet-wide
duplicate detection, certificate issuance, and revocation services remain open.
