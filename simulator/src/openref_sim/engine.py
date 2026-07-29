from __future__ import annotations

from heapq import heappop, heappush
from itertools import count
from typing import Callable

from .events import ScheduledEvent, TraceEvent


class Simulation:
    def __init__(self) -> None:
        self.now_us = 0
        self._events: list[ScheduledEvent] = []
        self._sequence = count()
        self.trace: list[TraceEvent] = []

    def schedule_at(
        self,
        time_us: int,
        callback: Callable[[], None],
        description: str = "",
    ) -> None:
        if time_us < self.now_us:
            raise ValueError("Cannot schedule an event in the past")
        heappush(
            self._events,
            ScheduledEvent(time_us, next(self._sequence), callback, description),
        )

    def schedule(
        self,
        delay_us: int,
        callback: Callable[[], None],
        description: str = "",
    ) -> None:
        if delay_us < 0:
            raise ValueError("delay_us must be nonnegative")
        self.schedule_at(self.now_us + delay_us, callback, description)

    def record(
        self,
        event: str,
        *,
        node_id: int | None = None,
        packet_id: int | None = None,
        **details: object,
    ) -> None:
        self.trace.append(
            TraceEvent(
                time_us=self.now_us,
                event=event,
                node_id=node_id,
                packet_id=packet_id,
                details=dict(details),
            )
        )

    def run(self, until_us: int) -> None:
        if until_us < self.now_us:
            raise ValueError("until_us cannot move simulation backwards")
        while self._events:
            event = heappop(self._events)
            if event.time_us > until_us:
                heappush(self._events, event)
                break
            self.now_us = event.time_us
            event.callback()
        self.now_us = until_us
