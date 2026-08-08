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
