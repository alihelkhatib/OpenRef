from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PacketKind(str, Enum):
    VOICE = "voice"
    HEARTBEAT = "heartbeat"


@dataclass(frozen=True)
class Packet:
    packet_id: int
    source_id: int
    sequence: int
    created_at_us: int
    payload_bytes: int
    kind: PacketKind = PacketKind.VOICE


def packet_airtime_us(payload_bytes: int, bitrate_bps: int, overhead_bytes: int, preamble_us: int = 0) -> int:
    if payload_bytes < 0 or overhead_bytes < 0:
        raise ValueError("Byte counts must be nonnegative")
    if bitrate_bps <= 0:
        raise ValueError("bitrate_bps must be positive")
    bits = (payload_bytes + overhead_bytes) * 8
    serialized_us = (bits * 1_000_000 + bitrate_bps - 1) // bitrate_bps
    return preamble_us + serialized_us
