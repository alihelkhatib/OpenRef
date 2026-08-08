from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import random

from .engine import Simulation
from .packet import Packet


@dataclass
class Transmission:
    packet: Packet
    start_us: int
    end_us: int
    collided: bool = False


TransmissionCallback = Callable[[bool, str | None], None]


class SharedMedium:
    """Single-channel medium with overlap collisions and deterministic random loss."""

    def __init__(
        self,
        simulation: Simulation,
        propagation_delay_us: int = 2,
        *,
        random_seed: int = 1,
        base_loss: float = 0.0,
    ) -> None:
        self.simulation = simulation
        self.propagation_delay_us = propagation_delay_us
        self.random = random.Random(random_seed)
        self.base_loss = base_loss
        self.loss_windows: list[tuple[int, int, float]] = []
        self.active: list[Transmission] = []

    def add_loss_window(self, start_us: int, duration_us: int, probability: float) -> None:
        self.loss_windows.append((start_us, start_us + duration_us, probability))

    def _loss_probability(self, time_us: int) -> float:
        probability = self.base_loss
        for start, end, candidate in self.loss_windows:
            if start <= time_us < end:
                probability = max(probability, candidate)
        return probability

    def transmit(
        self,
        packet: Packet,
        airtime_us: int,
        on_complete: TransmissionCallback | None = None,
    ) -> Transmission:
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
            kind=packet.kind.value,
        )

        def finish() -> None:
            self.active.remove(tx)
            delivered = False
            reason = None
            if tx.collided:
                reason = "collision"
                self.simulation.record(
                    "packet_collided",
                    node_id=packet.source_id,
                    packet_id=packet.packet_id,
                    kind=packet.kind.value,
                )
            elif self.random.random() < self._loss_probability(tx.start_us):
                reason = "random_loss"
                self.simulation.record(
                    "packet_lost",
                    node_id=packet.source_id,
                    packet_id=packet.packet_id,
                    kind=packet.kind.value,
                )
            else:
                delivered = True
                latency = self.simulation.now_us + self.propagation_delay_us - packet.created_at_us
                self.simulation.record(
                    "packet_delivered",
                    node_id=packet.source_id,
                    packet_id=packet.packet_id,
                    latency_us=latency,
                    kind=packet.kind.value,
                )
            if on_complete is not None:
                on_complete(delivered, reason)

        self.simulation.schedule(airtime_us, finish, "transmission complete")
        return tx
