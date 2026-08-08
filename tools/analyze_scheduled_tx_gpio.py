from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Iterable


TIME_COLUMNS = (
    "time_s",
    "time",
    "timestamp_s",
    "timestamp",
    "Time [s]",
    "Time",
)
CHANNEL_COLUMNS = ("channel", "Channel", "name", "Name")
VALUE_COLUMNS = ("value", "Value", "state", "State")


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


def _first_present(fieldnames: Iterable[str], candidates: Iterable[str]) -> str | None:
    names = set(fieldnames)
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _parse_time_us(value: str) -> float:
    text = value.strip()
    if not text:
        raise ValueError("empty timestamp")
    lowered = text.lower()
    multiplier = 1_000_000.0
    if lowered.endswith("us"):
        multiplier = 1.0
        lowered = lowered[:-2]
    elif lowered.endswith("µs"):
        multiplier = 1.0
        lowered = lowered[:-2]
    elif lowered.endswith("ms"):
        multiplier = 1_000.0
        lowered = lowered[:-2]
    elif lowered.endswith("s"):
        multiplier = 1_000_000.0
        lowered = lowered[:-1]
    return float(lowered.strip()) * multiplier


def _is_high(value: str) -> bool:
    return value.strip().lower() in {"1", "high", "true", "rising", "rise"}


def _edge_list_times(
    rows: list[dict[str, str]],
    *,
    time_column: str,
    channel_column: str,
    value_column: str | None,
    queue_channel: str,
    start_channel: str,
) -> tuple[list[float], list[float]]:
    queue_edges: list[float] = []
    start_edges: list[float] = []
    previous: dict[str, bool] = {}

    for row in rows:
        channel = row.get(channel_column, "").strip()
        if channel not in {queue_channel, start_channel}:
            continue

        if value_column is None or not row.get(value_column, "").strip():
            rising = True
        else:
            high = _is_high(row[value_column])
            rising = high and not previous.get(channel, False)
            previous[channel] = high

        if not rising:
            continue

        timestamp = _parse_time_us(row[time_column])
        if channel == queue_channel:
            queue_edges.append(timestamp)
        else:
            start_edges.append(timestamp)

    return queue_edges, start_edges


def _sampled_column_times(
    rows: list[dict[str, str]],
    *,
    time_column: str,
    queue_channel: str,
    start_channel: str,
) -> tuple[list[float], list[float]]:
    queue_edges: list[float] = []
    start_edges: list[float] = []
    previous_queue = False
    previous_start = False

    for row in rows:
        timestamp = _parse_time_us(row[time_column])
        queue_high = _is_high(row.get(queue_channel, "0"))
        start_high = _is_high(row.get(start_channel, "0"))
        if queue_high and not previous_queue:
            queue_edges.append(timestamp)
        if start_high and not previous_start:
            start_edges.append(timestamp)
        previous_queue = queue_high
        previous_start = start_high

    return queue_edges, start_edges


def pair_edges(queue_edges: list[float], start_edges: list[float]) -> list[float]:
    return pair_edge_report(queue_edges, start_edges)["launch_errors_us"]


def pair_edge_report(
    queue_edges: list[float],
    start_edges: list[float],
) -> dict[str, object]:
    launch_errors: list[float] = []
    orphan_start_edges = 0
    start_index = 0
    for queue_time in queue_edges:
        while start_index < len(start_edges) and start_edges[start_index] < queue_time:
            orphan_start_edges += 1
            start_index += 1
        if start_index >= len(start_edges):
            break
        launch_errors.append(start_edges[start_index] - queue_time)
        start_index += 1

    return {
        "launch_errors_us": launch_errors,
        "orphan_start_edges": orphan_start_edges,
        "unpaired_queue_edges": len(queue_edges) - len(launch_errors),
        "extra_start_edges": len(start_edges) - start_index,
    }


def analyze_gpio_csv(
    path: str | Path,
    *,
    queue_channel: str,
    start_channel: str,
    time_column: str | None = None,
    channel_column: str | None = None,
    value_column: str | None = None,
    expected_samples: int = 100,
    max_launch_error_us: float | None = None,
    fail_on_unpaired_edges: bool = False,
) -> dict[str, object]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if not rows:
        raise ValueError(f"{path} has no CSV data rows")

    resolved_time_column = time_column or _first_present(fieldnames, TIME_COLUMNS)
    if resolved_time_column is None:
        raise ValueError("Could not identify time column; pass --time-column")

    resolved_channel_column = channel_column or _first_present(fieldnames, CHANNEL_COLUMNS)
    resolved_value_column = value_column or _first_present(fieldnames, VALUE_COLUMNS)

    if resolved_channel_column is not None:
        queue_edges, start_edges = _edge_list_times(
            rows,
            time_column=resolved_time_column,
            channel_column=resolved_channel_column,
            value_column=resolved_value_column,
            queue_channel=queue_channel,
            start_channel=start_channel,
        )
        csv_shape = "edge-list"
    else:
        if queue_channel not in fieldnames or start_channel not in fieldnames:
            raise ValueError(
                "Could not identify channel columns; pass --channel-column for edge-list CSVs "
                "or use sampled columns named for --queue-channel and --start-channel"
            )
        queue_edges, start_edges = _sampled_column_times(
            rows,
            time_column=resolved_time_column,
            queue_channel=queue_channel,
            start_channel=start_channel,
        )
        csv_shape = "sampled-columns"

    edge_report = pair_edge_report(queue_edges, start_edges)
    launch_errors = edge_report["launch_errors_us"]
    pass_count = len(launch_errors) >= expected_samples
    pass_error = (
        True
        if max_launch_error_us is None
        else bool(launch_errors and max(launch_errors) <= max_launch_error_us)
    )
    unpaired_edge_count = (
        edge_report["orphan_start_edges"]
        + edge_report["unpaired_queue_edges"]
        + edge_report["extra_start_edges"]
    )
    pass_edge_hygiene = not fail_on_unpaired_edges or unpaired_edge_count == 0

    return {
        "csv": str(path),
        "csv_shape": csv_shape,
        "time_column": resolved_time_column,
        "queue_channel": queue_channel,
        "start_channel": start_channel,
        "queue_edges": len(queue_edges),
        "start_edges": len(start_edges),
        "paired_samples": len(launch_errors),
        "orphan_start_edges": edge_report["orphan_start_edges"],
        "unpaired_queue_edges": edge_report["unpaired_queue_edges"],
        "extra_start_edges": edge_report["extra_start_edges"],
        "fail_on_unpaired_edges": fail_on_unpaired_edges,
        "expected_samples": expected_samples,
        "pass": pass_count and pass_error and pass_edge_hygiene,
        "launch_error_min_us": min(launch_errors) if launch_errors else None,
        "launch_error_mean_us": (
            sum(launch_errors) / len(launch_errors) if launch_errors else None
        ),
        "launch_error_p95_us": percentile(launch_errors, 0.95),
        "launch_error_p99_us": percentile(launch_errors, 0.99),
        "launch_error_max_us": max(launch_errors) if launch_errors else None,
        "max_launch_error_limit_us": max_launch_error_us,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze OpenRef E0-03 scheduled-TX GPIO marker captures."
    )
    parser.add_argument("csv", type=Path)
    parser.add_argument("--queue-channel", default="PB3")
    parser.add_argument("--start-channel", default="PB2")
    parser.add_argument("--time-column")
    parser.add_argument("--channel-column")
    parser.add_argument("--value-column")
    parser.add_argument("--expected-samples", type=int, default=100)
    parser.add_argument("--max-launch-error-us", type=float)
    parser.add_argument(
        "--fail-on-unpaired-edges",
        action="store_true",
        help="Fail if queue/start edge counts include orphan or unpaired edges.",
    )
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if args.expected_samples < 1:
        parser.error("--expected-samples must be at least 1")

    summary = analyze_gpio_csv(
        args.csv,
        queue_channel=args.queue_channel,
        start_channel=args.start_channel,
        time_column=args.time_column,
        channel_column=args.channel_column,
        value_column=args.value_column,
        expected_samples=args.expected_samples,
        max_launch_error_us=args.max_launch_error_us,
        fail_on_unpaired_edges=args.fail_on_unpaired_edges,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")

    raise SystemExit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
