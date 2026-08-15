from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class NodeSpec:
    node_id: int
    drift_ppm: float = 0.0


@dataclass(frozen=True)
class FaultSpec:
    action: str
    time_us: int
    node_id: int | None = None
    duration_us: int = 0
    probability: float | None = None


@dataclass(frozen=True)
class Scenario:
    name: str
    duration_seconds: float
    nodes: tuple[NodeSpec, ...]
    frame_duration_ms: float
    encoded_bitrate_bps: int
    radio_bitrate_bps: int
    overhead_bytes: int
    security_overhead_bytes: int
    fixed_length_packets: bool
    preamble_us: int
    slot_spacing_us: int
    schedule_slots: int
    propagation_delay_us: int
    random_seed: int = 1
    packet_loss_probability: float = 0.0
    max_queue_frames: int = 4
    audio_deadline_ms: float = 100.0
    heartbeat_interval_ms: float = 100.0
    heartbeat_timeout_ms: float = 300.0
    election_delay_ms: float = 50.0
    initial_coordinator_id: int = 1
    faults: tuple[FaultSpec, ...] = field(default_factory=tuple)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def frame_interval_us(self) -> int:
        return round(self.frame_duration_ms * 1_000)

    @property
    def payload_bytes(self) -> int:
        bits = self.encoded_bitrate_bps * self.frame_duration_ms / 1_000
        return round(bits / 8)

    @property
    def wire_payload_bytes(self) -> int:
        return self.payload_bytes + self.security_overhead_bytes

    @property
    def heartbeat_wire_payload_bytes(self) -> int:
        plaintext_bytes = self.payload_bytes if self.fixed_length_packets else 8
        return plaintext_bytes + self.security_overhead_bytes

    @property
    def duration_us(self) -> int:
        return round(self.duration_seconds * 1_000_000)

    @property
    def audio_deadline_us(self) -> int:
        return round(self.audio_deadline_ms * 1_000)

    @property
    def heartbeat_interval_us(self) -> int:
        return round(self.heartbeat_interval_ms * 1_000)

    @property
    def heartbeat_timeout_us(self) -> int:
        return round(self.heartbeat_timeout_ms * 1_000)

    @property
    def election_delay_us(self) -> int:
        return round(self.election_delay_ms * 1_000)


def _nodes(raw: Any) -> tuple[NodeSpec, ...]:
    if isinstance(raw, int):
        return tuple(NodeSpec(i + 1) for i in range(raw))
    return tuple(
        NodeSpec(node_id=int(item["id"]), drift_ppm=float(item.get("drift_ppm", 0.0)))
        for item in raw
    )


def _faults(raw: list[dict[str, Any]] | None) -> tuple[FaultSpec, ...]:
    result: list[FaultSpec] = []
    for item in raw or []:
        result.append(
            FaultSpec(
                action=str(item["action"]),
                time_us=round(float(item.get("time_seconds", item.get("start_seconds", 0))) * 1_000_000),
                node_id=int(item["node_id"]) if "node_id" in item else None,
                duration_us=round(float(item.get("duration_seconds", 0)) * 1_000_000),
                probability=float(item["probability"]) if "probability" in item else None,
            )
        )
    return tuple(result)


def load_scenario(path: str | Path) -> Scenario:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    protocol = data.get("protocol", {})
    return Scenario(
        name=str(data["name"]),
        duration_seconds=float(data["duration_seconds"]),
        nodes=_nodes(data["nodes"]),
        frame_duration_ms=float(data["audio"]["frame_duration_ms"]),
        encoded_bitrate_bps=int(data["audio"]["encoded_bitrate_bps"]),
        radio_bitrate_bps=int(data["radio"]["bitrate_bps"]),
        overhead_bytes=int(data["radio"].get("overhead_bytes", 16)),
        security_overhead_bytes=int(data["radio"].get("security_overhead_bytes", 0)),
        fixed_length_packets=bool(data["radio"].get("fixed_length_packets", False)),
        preamble_us=int(data["radio"].get("preamble_us", 0)),
        slot_spacing_us=int(data["schedule"]["slot_spacing_us"]),
        schedule_slots=int(data["schedule"].get("total_slots", len(_nodes(data["nodes"])))),
        propagation_delay_us=int(data["radio"].get("propagation_delay_us", 2)),
        random_seed=int(data.get("random_seed", 1)),
        packet_loss_probability=float(data["radio"].get("packet_loss_probability", 0.0)),
        max_queue_frames=int(data["audio"].get("max_queue_frames", 4)),
        audio_deadline_ms=float(data["audio"].get("deadline_ms", 100.0)),
        heartbeat_interval_ms=float(protocol.get("heartbeat_interval_ms", 100.0)),
        heartbeat_timeout_ms=float(protocol.get("heartbeat_timeout_ms", 300.0)),
        election_delay_ms=float(protocol.get("election_delay_ms", 50.0)),
        initial_coordinator_id=int(protocol.get("initial_coordinator_id", 1)),
        faults=_faults(data.get("faults")),
    )
