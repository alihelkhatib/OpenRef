from __future__ import annotations

from dataclasses import dataclass

from .engine import Simulation
from .packet import Packet


@dataclass
class Transmission:
    packet: Packet
    start_us: int
    end_us: int
    collided: bool = False


class SharedMedium:
    """Single-channel medium using an all-overlaps-collide model."""

    def __init__(self, simulation: Simulation, propagation_delay_us: int = 2) -> None:
        self.simulation = simulation
        self.propagation_delay_us = propagation_delay_us
        self.active: list[Transmission] = []
        self.completed: list[Transmission] = []

    def transmit(self, packet: Packet, airtime_us: int) -> Transmission:
        tx = Transmission(packet, self.simulation.now_us, self.simulation.now_us + airtime_us)
        for active in self.active:
            if active.end_us > tx.start_us:
                active.collided = True
                tx.collided = True
                self.simulation.record(
                    "collision_detected",
                    node_id=packet.source_id,
                    packet_id=packet.packet_id,
                    with_packet_id=active.packet.packet_id,
                )
        self.active.append(tx)
        self.simulation.record(
            "tx_start",
            node_id=packet.source_id,
            packet_id=packet.packet_id,
            airtime_us=airtime_us,
        )

        def finish() -> None:
            self.active.remove(tx)
            self.completed.append(tx)
            if tx.collided:
                self.simulation.record(
                    "packet_collided",
                    node_id=packet.source_id,
                    packet_id=packet.packet_id,
                )
            else:
                self.simulation.record(
                    "packet_delivered",
                    node_id=packet.source_id,
                    packet_id=packet.packet_id,
                    latency_us=(self.simulation.now_us + self.propagation_delay_us)
                    - packet.created_at_us,
                )

        self.simulation.schedule(airtime_us, finish, "transmission complete")
        return tx
