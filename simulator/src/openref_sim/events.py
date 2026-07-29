from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(order=True)
class ScheduledEvent:
    time_us: int
    order: int
    callback: Callable[[], None] = field(compare=False)
    description: str = field(default="", compare=False)


@dataclass(frozen=True)
class TraceEvent:
    time_us: int
    event: str
    node_id: int | None = None
    packet_id: int | None = None
    details: dict[str, Any] = field(default_factory=dict)
