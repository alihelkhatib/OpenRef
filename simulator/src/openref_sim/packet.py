from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import struct


OPENREF_MAGIC = 0x4F52
OPENREF_PACKET_VERSION = 1
OPENREF_BROADCAST_ID = 0
OPENREF_HEADER_BYTES = 18
OPENREF_MAX_PAYLOAD_BYTES = 255
_HEADER = struct.Struct("<HBBBBHQH")


class PacketKind(str, Enum):
    VOICE = "voice"
    HEARTBEAT = "heartbeat"


class WirePacketKind(int, Enum):
    PING = 1
    AUDIO_FRAME = 2
    HEARTBEAT = 3
    CONTROL = 4


@dataclass(frozen=True)
class WireHeader:
    kind: WirePacketKind
    source_id: int
    destination_id: int
    sequence: int
    tx_timestamp_us: int
    payload_length: int

    def encode(self) -> bytes:
        _validate_header(self)
        return _HEADER.pack(
            OPENREF_MAGIC, OPENREF_PACKET_VERSION, self.kind.value,
            self.source_id, self.destination_id, self.sequence,
            self.tx_timestamp_us, self.payload_length,
        )

    @classmethod
    def decode(cls, data: bytes) -> "WireHeader":
        if len(data) < OPENREF_HEADER_BYTES:
            raise ValueError("packet is shorter than the OpenRef header")
        magic, version, kind, source, destination, sequence, timestamp, length = _HEADER.unpack_from(data)
        if magic != OPENREF_MAGIC:
            raise ValueError("invalid OpenRef packet magic")
        if version != OPENREF_PACKET_VERSION:
            raise ValueError("unsupported OpenRef packet version")
        try:
            packet_kind = WirePacketKind(kind)
        except ValueError as exc:
            raise ValueError("unknown OpenRef packet kind") from exc
        header = cls(packet_kind, source, destination, sequence, timestamp, length)
        _validate_header(header)
        if len(data) < OPENREF_HEADER_BYTES + length:
            raise ValueError("packet payload is truncated")
        return header


def _validate_header(header: WireHeader) -> None:
    if not 1 <= header.source_id <= 254:
        raise ValueError("source_id must identify a node from 1 through 254")
    if not 0 <= header.destination_id <= 254:
        raise ValueError("destination_id must be broadcast (0) or a node ID")
    if not 0 <= header.sequence <= 0xFFFF:
        raise ValueError("sequence must fit in 16 bits")
    if not 0 <= header.tx_timestamp_us <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("tx_timestamp_us must fit in 64 bits")
    if not 0 <= header.payload_length <= OPENREF_MAX_PAYLOAD_BYTES:
        raise ValueError("payload_length exceeds the Prototype 0 limit")


def encode_wire_packet(header: WireHeader, payload: bytes = b"") -> bytes:
    if len(payload) != header.payload_length:
        raise ValueError("payload length does not match the header")
    return header.encode() + payload


def decode_wire_packet(data: bytes) -> tuple[WireHeader, bytes]:
    header = WireHeader.decode(data)
    end = OPENREF_HEADER_BYTES + header.payload_length
    return header, data[OPENREF_HEADER_BYTES:end]


@dataclass(frozen=True)
class Packet:
    packet_id: int
    source_id: int
    sequence: int
    created_at_us: int
    payload_bytes: int
    kind: PacketKind = PacketKind.VOICE


def packet_airtime_us(
    payload_bytes: int,
    bitrate_bps: int,
    overhead_bytes: int,
    preamble_us: int = 0,
) -> int:
    if payload_bytes < 0 or overhead_bytes < 0:
        raise ValueError("Byte counts must be nonnegative")
    if bitrate_bps <= 0:
        raise ValueError("bitrate_bps must be positive")
    bits = (payload_bytes + overhead_bytes) * 8
    serialized_us = (bits * 1_000_000 + bitrate_bps - 1) // bitrate_bps
    return preamble_us + serialized_us
