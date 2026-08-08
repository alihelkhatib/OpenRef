from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from .events import TraceEvent


def percentile(values: list[int], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low, high = math.floor(index), math.ceil(index)
    if low == high:
        return float(ordered[low])
    fraction = index - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def summarize(trace: list[TraceEvent]) -> dict[str, object]:
    generated = sum(e.event == "voice_frame_generated" for e in trace)
    delivered_events = [e for e in trace if e.event == "packet_delivered" and e.details.get("kind") == "voice"]
    collided = sum(e.event == "packet_collided" and e.details.get("kind") == "voice" for e in trace)
    lost = sum(e.event == "packet_lost" and e.details.get("kind") == "voice" for e in trace)
    queue_overflows = sum(e.event == "queue_overflow" for e in trace)
    deadline_misses = sum(e.event == "audio_deadline_miss" for e in trace)
    coordinator_changes = [e for e in trace if e.event == "coordinator_selected" and e.details.get("previous_id") is not None]
    latencies = [int(e.details["latency_us"]) for e in delivered_events]
    depths = [int(e.details["depth"]) for e in trace if e.event == "queue_depth"]
    delivered = len(delivered_events)
    return {
        "generated": generated,
        "delivered": delivered,
        "collided": collided,
        "randomly_lost": lost,
        "queue_overflows": queue_overflows,
        "audio_deadline_misses": deadline_misses,
        "delivery_ratio": delivered / generated if generated else None,
        "mean_latency_us": sum(latencies) / len(latencies) if latencies else None,
        "p95_latency_us": percentile(latencies, 0.95),
        "p99_latency_us": percentile(latencies, 0.99),
        "max_latency_us": max(latencies) if latencies else None,
        "max_queue_depth": max(depths) if depths else 0,
        "coordinator_changes": len(coordinator_changes),
        "coordinator_recovery_time_us": max(
            (int(e.details.get("recovery_time_us", 0)) for e in coordinator_changes),
            default=None,
        ),
    }


def write_trace_csv(trace: list[TraceEvent], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["time_us", "event", "node_id", "packet_id", "details_json"],
        )
        writer.writeheader()
        for event in trace:
            writer.writerow(
                {
                    "time_us": event.time_us,
                    "event": event.event,
                    "node_id": event.node_id,
                    "packet_id": event.packet_id,
                    "details_json": json.dumps(event.details, sort_keys=True),
                }
            )
