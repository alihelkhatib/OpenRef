from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


TIME_COLUMNS = ("time_us", "timestamp_us", "local_time_us", "time", "Time [s]", "Time")
ID_COLUMNS = ("frame_id", "impulse_id", "sequence", "id")
EVENT_COLUMNS = ("event", "marker", "name", "Event", "Marker")

DEFAULT_EVENTS = {
    "impulse": "impulse",
    "capture": "capture_frame",
    "queue": "packet_queue",
    "tx_start": "tx_start",
    "rx": "rx_done",
    "playback": "playback_output",
}


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    fraction = index - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def _first_present(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in fieldnames:
            return candidate
    return None


def _parse_time_us(value: str) -> float:
    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")
    lowered = text.lower()
    multiplier = 1.0
    if lowered.endswith("us"):
        lowered = lowered[:-2]
    elif lowered.endswith("µs"):
        lowered = lowered[:-2]
    elif lowered.endswith("ms"):
        multiplier = 1_000.0
        lowered = lowered[:-2]
    elif lowered.endswith("s"):
        multiplier = 1_000_000.0
        lowered = lowered[:-1]
    return float(lowered.strip()) * multiplier


def _stats(values: list[float]) -> dict[str, float | None]:
    return {
        "min_us": min(values) if values else None,
        "mean_us": sum(values) / len(values) if values else None,
        "p95_us": percentile(values, 0.95),
        "p99_us": percentile(values, 0.99),
        "max_us": max(values) if values else None,
    }


def _load_events(
    path: Path,
    *,
    time_column: str | None,
    id_column: str | None,
    event_column: str | None,
) -> dict[str, dict[str, float]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not rows:
        raise ValueError(f"{path} has no CSV data rows")

    resolved_time_column = time_column or _first_present(fieldnames, TIME_COLUMNS)
    resolved_id_column = id_column or _first_present(fieldnames, ID_COLUMNS)
    resolved_event_column = event_column or _first_present(fieldnames, EVENT_COLUMNS)
    missing = [
        name
        for name, value in (
            ("time column", resolved_time_column),
            ("frame/impulse id column", resolved_id_column),
            ("event column", resolved_event_column),
        )
        if value is None
    ]
    if missing:
        raise ValueError(f"Could not identify {', '.join(missing)}")

    events_by_id: dict[str, dict[str, float]] = {}
    for row in rows:
        frame_id = row.get(resolved_id_column, "").strip()
        event = row.get(resolved_event_column, "").strip()
        timestamp_text = row.get(resolved_time_column, "").strip()
        if not frame_id or not event or not timestamp_text:
            continue
        events_by_id.setdefault(frame_id, {})
        events_by_id[frame_id][event] = _parse_time_us(timestamp_text)
    return events_by_id


def _delta(events: dict[str, float], start: str, end: str) -> float | None:
    if start not in events or end not in events:
        return None
    return events[end] - events[start]


def analyze_audio_loopback(
    path: str | Path,
    *,
    expected_samples: int = 10,
    target_latency_ms: float = 120.0,
    max_latency_ms: float = 180.0,
    time_column: str | None = None,
    id_column: str | None = None,
    event_column: str | None = None,
    events: dict[str, str] | None = None,
) -> dict[str, Any]:
    event_names = dict(DEFAULT_EVENTS)
    if events:
        event_names.update(events)

    events_by_id = _load_events(
        Path(path),
        time_column=time_column,
        id_column=id_column,
        event_column=event_column,
    )

    complete_frames: list[dict[str, Any]] = []
    missing_frames: list[dict[str, Any]] = []
    invalid_frames: list[dict[str, Any]] = []
    stage_values: dict[str, list[float]] = {
        "capture_latency": [],
        "queue_latency": [],
        "radio_latency": [],
        "playback_latency": [],
        "end_to_end_latency": [],
    }

    required_event_values = set(event_names.values())
    for frame_id, frame_events in sorted(events_by_id.items(), key=lambda item: item[0]):
        missing = sorted(required_event_values - set(frame_events))
        if missing:
            missing_frames.append({"frame_id": frame_id, "missing_events": missing})
            continue

        capture_latency = _delta(frame_events, event_names["impulse"], event_names["capture"])
        queue_latency = _delta(frame_events, event_names["capture"], event_names["queue"])
        radio_latency = _delta(frame_events, event_names["tx_start"], event_names["rx"])
        playback_latency = _delta(frame_events, event_names["rx"], event_names["playback"])
        end_to_end_latency = _delta(
            frame_events,
            event_names["impulse"],
            event_names["playback"],
        )
        latencies = {
            "capture_latency_us": capture_latency,
            "queue_latency_us": queue_latency,
            "radio_latency_us": radio_latency,
            "playback_latency_us": playback_latency,
            "end_to_end_latency_us": end_to_end_latency,
        }
        negative_stages = [
            key
            for key, value in latencies.items()
            if value is not None and value < 0
        ]
        if negative_stages:
            invalid_frames.append(
                {"frame_id": frame_id, "negative_stages": negative_stages}
            )
            continue
        complete_frames.append({"frame_id": frame_id, **latencies})
        for key, value in (
            ("capture_latency", capture_latency),
            ("queue_latency", queue_latency),
            ("radio_latency", radio_latency),
            ("playback_latency", playback_latency),
            ("end_to_end_latency", end_to_end_latency),
        ):
            if value is not None:
                stage_values[key].append(value)

    end_to_end = stage_values["end_to_end_latency"]
    p95 = percentile(end_to_end, 0.95)
    max_value = max(end_to_end) if end_to_end else None
    passed = (
        len(complete_frames) >= expected_samples
        and not invalid_frames
        and p95 is not None
        and p95 <= target_latency_ms * 1_000.0
        and max_value is not None
        and max_value <= max_latency_ms * 1_000.0
    )

    return {
        "csv": str(path),
        "expected_samples": expected_samples,
        "complete_samples": len(complete_frames),
        "incomplete_samples": len(missing_frames),
        "invalid_samples": len(invalid_frames),
        "target_latency_ms": target_latency_ms,
        "max_latency_ms": max_latency_ms,
        "pass": passed,
        "events": event_names,
        "capture_latency": _stats(stage_values["capture_latency"]),
        "queue_latency": _stats(stage_values["queue_latency"]),
        "radio_latency": _stats(stage_values["radio_latency"]),
        "playback_latency": _stats(stage_values["playback_latency"]),
        "end_to_end_latency": _stats(end_to_end),
        "missing_frames": missing_frames,
        "invalid_frames": invalid_frames,
        "frames": complete_frames,
    }


def _event_override(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("event overrides must use key=value")
    key, event_name = value.split("=", 1)
    if key not in DEFAULT_EVENTS:
        allowed = ", ".join(sorted(DEFAULT_EVENTS))
        raise argparse.ArgumentTypeError(f"unknown event key '{key}', expected one of {allowed}")
    if not event_name:
        raise argparse.ArgumentTypeError("event name must not be empty")
    return key, event_name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze OpenRef E0-07 audio loopback timing captures."
    )
    parser.add_argument("csv", type=Path)
    parser.add_argument("--expected-samples", type=int, default=10)
    parser.add_argument("--target-latency-ms", type=float, default=120.0)
    parser.add_argument("--max-latency-ms", type=float, default=180.0)
    parser.add_argument("--time-column")
    parser.add_argument("--id-column")
    parser.add_argument("--event-column")
    parser.add_argument(
        "--event",
        action="append",
        type=_event_override,
        default=[],
        help="Override an event label, for example --event playback=audio_out.",
    )
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if args.expected_samples < 1:
        parser.error("--expected-samples must be at least 1")
    if args.target_latency_ms <= 0 or args.max_latency_ms <= 0:
        parser.error("latency limits must be positive")

    summary = analyze_audio_loopback(
        args.csv,
        expected_samples=args.expected_samples,
        target_latency_ms=args.target_latency_ms,
        max_latency_ms=args.max_latency_ms,
        time_column=args.time_column,
        id_column=args.id_column,
        event_column=args.event_column,
        events=dict(args.event),
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")

    raise SystemExit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
