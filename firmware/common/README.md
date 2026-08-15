# Firmware Common

This directory holds vendor-independent firmware contracts for Prototype 0.

Code in this directory must not include Silicon Labs, TI, or other vendor SDK
headers. Vendor adapters translate these contracts into SDK calls.

## Packet Wire Format

`openref_proto0_packet_header_t` is serialized explicitly by
`openref_proto0_packet.c`; do not transmit the C struct directly. The wire
header is 18 bytes:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 2 | magic, little-endian |
| 2 | 1 | version |
| 3 | 1 | kind |
| 4 | 1 | source ID |
| 5 | 1 | destination ID |
| 6 | 2 | sequence, little-endian |
| 8 | 8 | TX timestamp us, little-endian |
| 16 | 2 | payload length, little-endian |

## Network State Machine

`openref_network.h/.c` implements the vendor-independent six-node TDMA schedule,
coordinator timeout/election state, and bounded per-source receive counters. It
does not include vendor SDK headers or allocate memory dynamically.

`openref_network_packet.h/.c` provides fixed 98-byte audio and heartbeat frames:
an 18-byte network header plus the 80-byte payload required for two consecutive
40-byte LC3 frames.

`openref_security.h/.c` defines the 13-byte AES-CCM nonce construction and the
per-source 64-packet authenticated replay window. Protection adds an 8-byte
counter prefix and 8-byte tag, producing a 96-byte secured payload and 114-byte
radio packet. A platform crypto adapter must authenticate before replay
admission; this portable layer intentionally contains no AES implementation.

`openref_boot_counter.h/.c` advances a monotonic boot counter through storage
callbacks and reads it back before allowing nonce use.
`openref_secure_network_packet.h/.c` converts the proven 98-byte plaintext
representation to and from the 114-byte protected wire representation while
leaving the network state machine independent of the crypto backend.

## Audio Processor Link

`openref_audio_link.h/.c` defines the fixed 98-byte, CRC-protected internal SPI
frame that carries two 40-byte LC3 frames between the radio and audio
processors. It also provides a statically allocated four-entry queue that drops
the oldest frame on overflow and reports cumulative push, pop, and overrun
counters.
