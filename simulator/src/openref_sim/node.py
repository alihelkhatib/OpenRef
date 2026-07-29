from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import count

from .engine import Simulation
from .medium import SharedMedium
from .packet import Packet, PacketKind, packet_airtime_us


@dataclass(frozen=True)
class NodeConfig:
    node_id: int
    slot_offset_us: int
    drift_ppm: float = 0.0


class VoiceNode:
    def __init__(self, simulation: Simulation, medium: SharedMedium, config: NodeConfig, *, frame_interval_us: int, payload_bytes: int, bitrate_bps: int, overhead_bytes: int, preamble_us: int, packet_ids: count, stop_generation_at_us: int, max_queue_frames: int, deadline_us: int) -> None:
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
        self.max_queue_frames = max_queue_frames
        self.deadline_us = deadline_us
        self.sequence = 0
        self.queue: deque[Packet] = deque()
        self.enabled = True
        self.max_queue_depth = 0
        self.local_period_us = max(1, round(frame_interval_us / (1 + config.drift_ppm / 1_000_000)))

    def start(self) -> None:
        self.simulation.schedule_at(self.config.slot_offset_us, self._generate, f"node {self.config.node_id} first frame")
        self.simulation.schedule_at(self.config.slot_offset_us, self._slot, f"node {self.config.node_id} first slot")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.simulation.record("node_enabled" if enabled else "node_disabled", node_id=self.config.node_id)

    def _generate(self) -> None:
        if self.enabled:
            packet = Packet(next(self.packet_ids), self.config.node_id, self.sequence, self.simulation.now_us, self.payload_bytes)
            self.sequence += 1
            self.simulation.record("voice_frame_generated", node_id=self.config.node_id, packet_id=packet.packet_id, sequence=packet.sequence)
            if len(self.queue) >= self.max_queue_frames:
                dropped = self.queue.popleft()
                self.simulation.record("queue_overflow", node_id=self.config.node_id, packet_id=dropped.packet_id)
            self.queue.append(packet)
            self.max_queue_depth = max(self.max_queue_depth, len(self.queue))
            self.simulation.record("queue_depth", node_id=self.config.node_id, depth=len(self.queue))
        next_time = self.simulation.now_us + self.local_period_us
        if next_time < self.stop_generation_at_us:
            self.simulation.schedule_at(next_time, self._generate, f"node {self.config.node_id} next frame")

    def _slot(self) -> None:
        if self.enabled and self.queue:
            packet = self.queue.popleft()
            age = self.simulation.now_us - packet.created_at_us
            if age > self.deadline_us:
                self.simulation.record("audio_deadline_miss", node_id=self.config.node_id, packet_id=packet.packet_id, age_us=age, stage="queue")
            airtime = packet_airtime_us(self.payload_bytes, self.bitrate_bps, self.overhead_bytes, self.preamble_us)
            def complete(delivered: bool, reason: str | None) -> None:
                if delivered:
                    latency = self.simulation.now_us + self.medium.propagation_delay_us - packet.created_at_us
                    if latency > self.deadline_us:
                        self.simulation.record("audio_deadline_miss", node_id=self.config.node_id, packet_id=packet.packet_id, age_us=latency, stage="delivery")
            self.medium.transmit(packet, airtime, complete)
        next_time = self.simulation.now_us + self.local_period_us
        if next_time < self.stop_generation_at_us:
            self.simulation.schedule_at(next_time, self._slot, f"node {self.config.node_id} next slot")
