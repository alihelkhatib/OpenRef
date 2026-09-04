# Local Service Access

**Document ID:** OR-ICD-010
**Revision:** 0.1
**Status:** Portable authorization policy implemented; utility and credential backend pending

## Boundary

Connecting a cable or fixture does not authorize access. The wearable issues a
fresh 32-byte challenge from its secure random source. The service utility
authenticates a transcript binding that challenge, a strictly increasing
counter, credential role, and exact requested permission mask. The target
credential backend verifies the response and durably advances the counter
before the session becomes active.

No password, private key, credential blob, or response is placed in diagnostics.
The portable layer treats the authentication response as opaque and wipes the
challenge after use.

## Permissions and roles

| Permission | Field role | Technician role | Factory role | Physical presence |
|---|---:|---:|---:|---:|
| Diagnostic export | yes | yes | yes | no |
| Configuration read | yes | yes | yes | no |
| Signed update staging | yes | yes | yes | no |
| Configuration write | no | yes | yes | required |
| Factory test | no | no | yes | required |
| Identity operation | no | no | yes | required |

Permission checks accept exactly one permission bit at a time. A role may
request a subset of its authority but cannot gain unrequested permissions.
Update access does not bypass `OR-ICD-008`; every package remains locally signed
and verified. Identity access does not bypass `OR-MFG-003` lifecycle gates.

## Lifetime and abuse handling

Challenges and sessions have independent bounded lifetimes. Responses with a
stale/replayed counter, expired challenge, excessive role, absent required
physical presence, invalid authenticator, or failed counter persistence are
rejected. After a configured number of consecutive failures, new challenges
are blocked for a bounded lockout interval. Monotonic-clock rollback ends any
active session and denies the operation. Explicit disconnect or service exit
wipes session authority immediately.

Authentication failures may record only a bounded reason/category through
`OPENREF_EVENT_SERVICE_AUTH_FAILURE`; challenge/response bytes and credential
identifiers are excluded.

`firmware/system/common/openref_service_session.h/.c` implements the portable
policy. Promotion requires a reviewed credential scheme, secure counter store,
secure RNG, USB/fixture transport limits, challenge replay tests across reset,
physical-presence bypass attempts, fuzzing, and confirmation that communication
remains unavailable or safely degraded during privileged maintenance.
