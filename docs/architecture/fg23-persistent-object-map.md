# FG23 Persistent Object Map

**Document ID:** OR-ARC-019
**Revision:** 0.1
**Status:** Prototype target allocation

The FG23 target reserves the following NVM3 keys. They are security-sensitive
monotonic state and may not be reused for configuration, diagnostics, or vendor
example data.

| NVM3 key | Object | Update rule | Failure behavior |
|---:|---|---|---|
| `0x0f5201` | Packet-nonce boot counter | increment and verify once before protected TX after boot | protected TX disabled |
| `0x0f5202` | Coordinator epoch | stored value must match current; increment and verify before coordinator promotion | remain in election |
| `0x0f5203` | Crew-admission counter | invitation counter must be strictly greater; write and verify before key activation | reject invitation |
| `0x0f5204` | Service-session counter | authenticator counter must be strictly greater; write and verify before granting permission | reject service session |
| `0x0f5210` | Configuration slot A | portable 80-byte generation/CRC record | fall back to slot B or defaults |
| `0x0f5211` | Configuration slot B | portable 80-byte generation/CRC record | fall back to slot A or defaults |
| `0x0f5220` | Boot-policy state slot A | portable 12-byte generation/CRC record | fall back to slot B; inhibit update/trial transition if neither is valid |
| `0x0f5221` | Boot-policy state slot B | portable 12-byte generation/CRC record | fall back to slot A; inhibit update/trial transition if neither is valid |
| `0x0f5230` | Device-lifecycle record slot A | portable 36-byte generation/CRC record | fall back to slot B; prohibit manufacturing progression if neither is valid |
| `0x0f5231` | Device-lifecycle record slot B | portable 36-byte generation/CRC record | fall back to slot A; prohibit manufacturing progression if neither is valid |

Monotonic objects are four-byte little-endian values stored through NVM3
data-object APIs. Missing monotonic objects initialize semantically to zero, but zero is never an
accepted persisted authorization counter. Corrupt type/length, read failure,
write failure, readback mismatch, or exhaustion fails closed at the consuming
policy. No factory image may silently erase one monotonic object while retaining
the associated credential or key.

Configuration slots are fixed 80-byte opaque records owned by `OR-ICD-009`;
their magic, schema, payload length, generation, and CRC are checked above the
NVM3 adapter. A missing or corrupt slot is invalid independently and cannot
damage the other slot.

Boot-policy slots use their own schema and magic, independent of configuration.
The portable store validates both copies and permits runtime persistence only
after loading valid prior state; factory initialization is a separate explicit
operation. If neither copy is valid, normal boot-state mutation fails closed.

The overlay switches are `-EnablePersistentEpoch`,
`-EnablePersistentSecurityCounters`, `-EnablePersistentConfig`,
`-EnablePersistentBootState`, and `-EnablePersistentDeviceRecord`. The boot
counter is independently enabled
with the protected-radio security configuration. Before production, the final
NVM layout must include vendor/system reservations, erase-page interaction,
wear/endurance analysis, power-cut testing for each object, migration rules, and
factory-reset/retirement behavior.
