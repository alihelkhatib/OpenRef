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

The Silicon Labs-specific adapter and app entry point are still pending. Keep
SDK includes out of these files; bridge to RAIL from a separate adapter file.
