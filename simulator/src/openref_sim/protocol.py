from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .engine import Simulation
from .medium import SharedMedium
from .packet import Packet, PacketKind, packet_airtime_us
from .node import VoiceNode


@dataclass(frozen=True)
class CoordinatorConfig:
    initial_coordinator_id: int
    heartbeat_interval_us: int
    heartbeat_timeout_us: int
    election_delay_us: int
    bitrate_bps: int
    overhead_bytes: int
    preamble_us: int
    heartbeat_payload_bytes: int = 8
    first_heartbeat_delay_us: int = 16_000

    @property
    def heartbeat_airtime_us(self) -> int:
        return packet_airtime_us(
            self.heartbeat_payload_bytes,
            self.bitrate_bps,
            self.overhead_bytes,
            self.preamble_us,
        )


class CoordinatorProtocol:
    def __init__(
        self,
        simulation: Simulation,
        medium: SharedMedium,
        nodes: dict[int, VoiceNode],
        config: CoordinatorConfig,
        packet_ids: Iterator[int],
    ) -> None:
        self.sim = simulation
        self.medium = medium
        self.nodes = nodes
        self.config = config
        self.coordinator_id = config.initial_coordinator_id
        self.packet_ids = packet_ids
        self.last_heartbeat_us = 0
        self.election_pending = False

    def start(self) -> None:
        self.sim.record("coordinator_selected", node_id=self.coordinator_id, previous_id=None)
        self.sim.schedule(self.config.first_heartbeat_delay_us, self._heartbeat)
        self.sim.schedule(self.config.heartbeat_timeout_us, self._check_timeout)

    def _heartbeat(self) -> None:
        node = self.nodes[self.coordinator_id]
        if node.enabled:
            packet = Packet(
                next(self.packet_ids),
                self.coordinator_id,
                0,
                self.sim.now_us,
                self.config.heartbeat_payload_bytes,
                PacketKind.HEARTBEAT,
            )

            def complete(delivered: bool, _reason: str | None) -> None:
                if delivered:
                    self.last_heartbeat_us = self.sim.now_us
                    self.sim.record(
                        "heartbeat_received",
                        node_id=self.coordinator_id,
                        packet_id=packet.packet_id,
                    )

            self.medium.transmit(packet, self.config.heartbeat_airtime_us, complete)
        self.sim.schedule(self.config.heartbeat_interval_us, self._heartbeat)

    def _check_timeout(self) -> None:
        heartbeat_age_us = self.sim.now_us - self.last_heartbeat_us
        if heartbeat_age_us > self.config.heartbeat_timeout_us and not self.election_pending:
            self.election_pending = True
            self.sim.record("heartbeat_timeout", node_id=self.coordinator_id)
            self.sim.schedule(self.config.election_delay_us, self._elect)
        self.sim.schedule(
            max(1, self.config.heartbeat_interval_us // 2),
            self._check_timeout,
        )

    def _elect(self) -> None:
        active = sorted(node_id for node_id, node in self.nodes.items() if node.enabled)
        old = self.coordinator_id
        if active:
            self.coordinator_id = active[0]
            self.last_heartbeat_us = self.sim.now_us
            self.sim.record(
                "coordinator_selected",
                node_id=self.coordinator_id,
                previous_id=old,
                recovery_time_us=self.config.election_delay_us,
            )
        self.election_pending = False
