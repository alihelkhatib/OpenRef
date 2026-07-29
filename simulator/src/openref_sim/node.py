from __future__ import annotations

from dataclasses import dataclass
from itertools import count

from .engine import Simulation
from .medium import SharedMedium
from .packet import Packet, packet_airtime_us


@dataclass(frozen=True)
class NodeConfig:
    node_id: int
    slot_offset_us: int


class VoiceNode:
    def __init__(
        self,
        simulation: Simulation,
        medium: SharedMedium,
        config: NodeConfig,
        *,
        frame_interval_us: int,
        payload_bytes: int,
        bitrate_bps: int,
        overhead_bytes: int,
        preamble_us: int,
        packet_ids: count,
        stop_generation_at_us: int,
    ) -> None:
        self.simulation = simulation
        self.medium = medium
        self.config = config
        self.frame_interval_us = frame_interval_us
        self.payload_bytes = payload_bytes
        self.bitrate_bps = bitrate_bps
        self.overhead_bytes = overhead_bytes
        self.preamble_us = preamble_us
        self.packet_ids = packet_ids
        self.stop_generation_at_us = stop_generation_at_us
        self.sequence = 0

    def start(self) -> None:
        self.simulation.schedule_at(
            self.config.slot_offset_us,
            self._generate_and_transmit,
            f"node {self.config.node_id} first frame",
        )

    def _generate_and_transmit(self) -> None:
        packet = Packet(
            packet_id=next(self.packet_ids),
            source_id=self.config.node_id,
            sequence=self.sequence,
            created_at_us=self.simulation.now_us,
            payload_bytes=self.payload_bytes,
        )
        self.sequence += 1
        self.simulation.record(
            "voice_frame_generated",
            node_id=self.config.node_id,
            packet_id=packet.packet_id,
            sequence=packet.sequence,
        )
        airtime_us = packet_airtime_us(
            self.payload_bytes,
            self.bitrate_bps,
            self.overhead_bytes,
            self.preamble_us,
        )
        self.medium.transmit(packet, airtime_us)
        next_time = self.simulation.now_us + self.frame_interval_us
        if next_time < self.stop_generation_at_us:
            self.simulation.schedule_at(
                next_time,
                self._generate_and_transmit,
                f"node {self.config.node_id} next frame",
            )
