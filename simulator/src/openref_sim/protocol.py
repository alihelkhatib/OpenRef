from __future__ import annotations

from itertools import count

from .engine import Simulation
from .medium import SharedMedium
from .packet import Packet, PacketKind, packet_airtime_us
from .node import VoiceNode


class CoordinatorProtocol:
    def __init__(self, simulation: Simulation, medium: SharedMedium, nodes: dict[int, VoiceNode], *, initial_coordinator_id: int, heartbeat_interval_us: int, heartbeat_timeout_us: int, election_delay_us: int, packet_ids: count, bitrate_bps: int, overhead_bytes: int, preamble_us: int) -> None:
        self.sim = simulation
        self.medium = medium
        self.nodes = nodes
        self.coordinator_id = initial_coordinator_id
        self.heartbeat_interval_us = heartbeat_interval_us
        self.heartbeat_timeout_us = heartbeat_timeout_us
        self.election_delay_us = election_delay_us
        self.packet_ids = packet_ids
        self.bitrate_bps = bitrate_bps
        self.overhead_bytes = overhead_bytes
        self.preamble_us = preamble_us
        self.last_heartbeat_us = 0
        self.election_pending = False

    def start(self) -> None:
        self.sim.record("coordinator_selected", node_id=self.coordinator_id, previous_id=None)
        self.sim.schedule(16_000, self._heartbeat)
        self.sim.schedule(self.heartbeat_timeout_us, self._check_timeout)

    def _heartbeat(self) -> None:
        node = self.nodes[self.coordinator_id]
        if node.enabled:
            packet = Packet(next(self.packet_ids), self.coordinator_id, 0, self.sim.now_us, 8, PacketKind.HEARTBEAT)
            airtime = packet_airtime_us(8, self.bitrate_bps, self.overhead_bytes, self.preamble_us)
            def complete(delivered: bool, reason: str | None) -> None:
                if delivered:
                    self.last_heartbeat_us = self.sim.now_us
                    self.sim.record("heartbeat_received", node_id=self.coordinator_id, packet_id=packet.packet_id)
            self.medium.transmit(packet, airtime, complete)
        self.sim.schedule(self.heartbeat_interval_us, self._heartbeat)

    def _check_timeout(self) -> None:
        if self.sim.now_us - self.last_heartbeat_us > self.heartbeat_timeout_us and not self.election_pending:
            self.election_pending = True
            self.sim.record("heartbeat_timeout", node_id=self.coordinator_id)
            self.sim.schedule(self.election_delay_us, self._elect)
        self.sim.schedule(max(1, self.heartbeat_interval_us // 2), self._check_timeout)

    def _elect(self) -> None:
        active = sorted(node_id for node_id, node in self.nodes.items() if node.enabled)
        old = self.coordinator_id
        if active:
            self.coordinator_id = active[0]
            self.last_heartbeat_us = self.sim.now_us
            self.sim.record("coordinator_selected", node_id=self.coordinator_id, previous_id=old, recovery_time_us=self.election_delay_us)
        self.election_pending = False
