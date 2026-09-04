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
| `openref_network_fg23.h/.c` | Opt-in scheduled RAIL transport for fixed-length synthetic audio and coordinator heartbeats. |
| `openref_lc3_benchmark.h/.c` | Opt-in one-encoder/five-decoder LC3 timing and memory benchmark. |
| `openref_security_fg23.h/.c` | Feature-gated Silicon Labs SE Manager AES-CCM adapter with no embedded key. |
| `openref_boot_counter_fg23.h/.c` | Feature-gated, fail-closed NVM3 boot-counter adapter. |
| `openref_audio_link_fg23.h/.c` | FG23 controller seam for persistent 98-byte SPI/DMA buffers, AUDIO_REQn service, ISR handoff, start retry, timeout abort, and peer-reset hold. |
| `openref_audio_link_fg23_sdk.h/.c` | Opt-in ICD-005 EUSART1/LDMA/GPIO binding for PA7, PA8, and PB0-PB3. |
| `openref_watchdog_fg23.h/.c` | Portable-gate target seam that extends the wrapping RAIL clock and feeds hardware only after required progress. |
| `openref_watchdog_fg23_sdk.h/.c` | Feature-gated WDOG0/ULFRCO binding for the Silicon Labs SDK. |

`openref_audio_link_fg23` contains no vendor calls. Bind its hooks to the
selected USART/LDMA instance and GPIO allocation in the generated target
project. The hook contract uses logical `request_asserted` and
`set_peer_reset(asserted)` values, so active-low electrical polarity remains in
the board binding. DMA completion must call
`openref_audio_fg23_transfer_complete_isr()` exactly once; parsing and queue
mutation remain in the main-loop `openref_audio_fg23_process()` call.

Enable the provisional hardware binding with `-EnableAudioLink`. It uses
EUSART1 (leaving EUSART0 for board VCOM), SPI mode 0 at 8 MHz, two DMA-manager
channels with descriptors allocated once at startup, software CSn, active-low
AUDIO_REQn, and active-low AUDIO_RESETn. CSn stays asserted until both DMA
transfers and EUSART `TXC` complete. The switch is disabled by default because
BRD2600A peripheral conflicts, the final processor pinout, SPI mode/polarity,
pin drive, request timing, and signal integrity still require schematic review
and bench validation. A successful SDK link is not electrical validation.

Enable the FG23 watchdog overlay with `-EnableWatchdog -EmlibSourceRoot <path>`.
The installer copies the SDK's Zlib-licensed `em_wdog.c` into the ignored local
overlay; it is not redistributed by OpenRef. The current application registers
the cooperative main loop as the first required progress source. WDOG0 runs
from ULFRCO through EM1/EM2, is locked until reset, and is configured for the
smallest hardware period not shorter than 2,000 ms (2,049 ULFRCO periods).
Deliberately stalling the loop and proving WDOG0 reset cause and elapsed time
still requires a flashed board and captured serial or debugger evidence.

The security adapter is inert unless `OPENREF_APP_SECURITY` is defined. Enabling
it requires the SDK `se_manager` component, a provisioned session key, and
monotonic persistent boot-counter storage; it deliberately has no fallback key.
