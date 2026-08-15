# FG23 Source Placeholder

Place OpenRef-owned Prototype 0 source files here after the first vendor example
is built and the SDK license/source record is captured in `../vendor-notes.md`.

Expected early files:

- `main.c` for mode selection and structured logging;
- `openref_radio_silabs.c` implementing `firmware/common/openref_radio.h`;
- `openref_proto0_packet.c` for packet encode/decode helpers;
- `gpio_markers.c` for timing-marker pins.

Do not paste large vendor example files here without recording their origin and
license.

## Current OpenRef-Owned Files

| File | Purpose |
|---|---|
| `openref_packet_pair.h` | Packet-pair state and app-level TX/RX helper API. |
| `openref_packet_pair.c` | Vendor-independent packet construction and RX sequence-gap tracking. |
| `../../common/openref_network.h/.c` | Vendor-independent six-node TDMA and coordinator state machine installed by the overlay script. |
| `openref_network_fg23.h/.c` | Opt-in scheduled RAIL transport with an optional secured 114-byte radio path. |
| `openref_lc3_benchmark.h/.c` | Opt-in one-encoder/five-decoder LC3 timing and memory benchmark. |
| `openref_security_fg23.h/.c` | Feature-gated Silicon Labs SE Manager AES-CCM adapter with no embedded key. |
| `openref_boot_counter_fg23.h/.c` | Feature-gated, fail-closed NVM3 boot-counter adapter. |
| `openref_network_epoch_fg23.h/.c` | Separately keyed, verified NVM3 coordinator-epoch adapter. |
| `openref_security_counters_fg23.h/.c` | Separate admission/service replay-counter domains with verified NVM3 writes. |
| `openref_config_store_fg23.h/.c` | Two-slot NVM3 backend for the portable versioned configuration store. |
| `openref_boot_state_store_fg23.h/.c` | Two-slot NVM3 backend for durable update/boot-policy state. |
| `openref_watchdog_fg23.h/.c` | Locked FG23 hardware-watchdog backend for the portable progress gate. |
| `openref_reset_cause_fg23.h/.c` | Capture-once raw and classified FG23 reset attribution. |
| `openref_device_record_store_fg23.h/.c` | Isolated two-slot NVM3 backend for manufacturing lifecycle state. |
| `openref_radio_session_fg23.h/.c` | Crew-key backend bridge to secured network provisioning and abort/wipe. |
| `openref_secure_startup_fg23.h/.c` | Joins verified NVM3 boot-counter advancement to the radio-session bridge. |

The security adapter is inert unless `OPENREF_APP_SECURITY` is defined. Enabling
it requires the SDK `se_manager` component, a provisioned session key, and
monotonic persistent boot-counter storage; it deliberately has no fallback key.

The overlay switch `-EnableSecureNetwork` requires `-EnableNetwork` and selects
the authenticated radio path. Crew admission must call
`openref_network_fg23_configure_security()` with a nonzero session ID, an
advanced persistent boot counter, a nonzero packet-counter start, and the
admitted key. Until then the adapter reports `SecurityNotProvisioned` once and
sends nothing. The generated project must include the SDK `se_manager` and
`nvm3_default` components; secure mode enables the verified NVM3 boot-counter
adapter automatically. The overlay does not rewrite the `.slcp` component
graph. No fixed development key or insecure fallback exists.

Product-style coordinator election defines `OPENREF_APP_NETWORK_EPOCH_NVM3`,
sets `require_persisted_epoch`, and assigns
`openref_network_epoch_fg23_advance` as the epoch callback. The adapter uses
NVM3 key `0x0f5202`, distinct from boot-counter key `0x0f5201`, rejects stored
state that does not match the in-memory current epoch, and verifies every write
before returning the next epoch. The disabled build always fails closed.

`-EnablePersistentBootState` defines `OPENREF_APP_BOOT_STATE_NVM3` and connects
the portable boot-state store to exact-length NVM3 objects `0x0f5220` and
`0x0f5221`. Record validation, generations, CRC, and verified readback remain
owned by the portable layer; the adapter fails closed when disabled.

`-EnableHardwareWatchdog` defines `OPENREF_APP_WATCHDOG_FG23`. Configuration
selects the first discrete FG23 watchdog period not shorter than the requested
timeout, records the resulting nominal value, runs through EM1/EM2/EM3, stops
during debugger halt, and locks configuration until reset. The period values
assume the documented nominal 1 kHz watchdog clock; production limits require
measured oscillator tolerance and injected-hang reset timing.

In the FG23 application, watchdog progress is reported only after the network
and optional LC3 processing paths return. A stalled path therefore withholds the
next feed. For controlled bench validation only,
`-WatchdogTestHangAfterFeeds N` (with `-EnableHardwareWatchdog`) prints an
`InjectedHang` marker and intentionally stops after `N` successful feeds. This
test option must never be enabled in a release image.

For logic-analyzer timing, `-WatchdogHangMarker PB3` drives a marker high
immediately before the intentional loop, while `-WatchdogBootMarker PB2` emits
a pulse at the beginning of the next application initialization. Marker pins
are optional and must match the board's actual soldered test connections.

Watchdog-enabled images also define `OPENREF_APP_RESET_CAUSE_FG23`. At startup,
the application reads and classifies the hardware reset-cause register before
clearing it, then emits both the raw mask and a stable portable classification.
Multiple simultaneous causes are preserved. Unknown bits remain visible and
set the `UNKNOWN` classification instead of being discarded.

`-EnablePersistentDeviceRecord` maps the explicit 36-byte portable lifecycle
payload to independently recoverable NVM3 records at `0x0f5230` and
`0x0f5231`. Private identity material is never included; only the public device
ID, public fingerprint, lifecycle state, generation, and failure code are stored.
