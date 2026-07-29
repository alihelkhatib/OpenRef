from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Scenario:
    name: str
    duration_seconds: float
    node_count: int
    frame_duration_ms: float
    encoded_bitrate_bps: int
    radio_bitrate_bps: int
    overhead_bytes: int
    preamble_us: int
    slot_spacing_us: int
    propagation_delay_us: int

    @property
    def frame_interval_us(self) -> int:
        return round(self.frame_duration_ms * 1_000)

    @property
    def payload_bytes(self) -> int:
        bits = self.encoded_bitrate_bps * self.frame_duration_ms / 1_000
        return round(bits / 8)

    @property
    def duration_us(self) -> int:
        return round(self.duration_seconds * 1_000_000)


def load_scenario(path: str | Path) -> Scenario:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Scenario(
        name=str(data["name"]),
        duration_seconds=float(data["duration_seconds"]),
        node_count=int(data["nodes"]),
        frame_duration_ms=float(data["audio"]["frame_duration_ms"]),
        encoded_bitrate_bps=int(data["audio"]["encoded_bitrate_bps"]),
        radio_bitrate_bps=int(data["radio"]["bitrate_bps"]),
        overhead_bytes=int(data["radio"].get("overhead_bytes", 16)),
        preamble_us=int(data["radio"].get("preamble_us", 0)),
        slot_spacing_us=int(data["schedule"]["slot_spacing_us"]),
        propagation_delay_us=int(data["radio"].get("propagation_delay_us", 2)),
    )
