from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def percentile(values: list[int], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return float(ordered[low])
    fraction = index - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def _detail_value(detail: str, key: str) -> str | None:
    prefix = f"{key}="
    for token in detail.split():
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def analyze(
    path: str | Path,
    *,
    min_received: int | None = None,
    expected_first_sequence: int | None = None,
    expected_last_sequence: int | None = None,
    max_sequence_gaps: int | None = None,
    max_rx_gap_events: int | None = None,
    max_fault_events: int | None = None,
    max_boot_events: int | None = None,
    max_inter_arrival_us: int | None = None,
) -> dict[str, object]:
    rx_sequences: list[int] = []
    rx_times: list[int] = []
    rssi_values: list[int] = []
    lqi_values: list[int] = []
    boot_count = 0
    fault_count = 0
    gap_events = 0

    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            event = row.get("event", "")
            if event == "boot":
                boot_count += 1
            elif event == "fault":
                fault_count += 1
            elif event == "rx_gap":
                gap_events += 1
            elif event == "rx_done":
                sequence = row.get("sequence", "")
                local_time_us = row.get("local_time_us", "")
                if sequence:
                    rx_sequences.append(int(sequence))
                if local_time_us:
                    rx_times.append(int(local_time_us))

                detail = row.get("detail", "")
                rssi = _detail_value(detail, "rssi")
                lqi = _detail_value(detail, "lqi")
                if rssi is not None:
                    rssi_values.append(int(rssi))
                if lqi is not None:
                    lqi_values.append(int(lqi))

    sequence_gaps = 0
    if rx_sequences:
        ordered = sorted(rx_sequences)
        for previous, current in zip(ordered, ordered[1:]):
            if current > previous + 1:
                sequence_gaps += current - previous - 1

    inter_arrival_us = [
        current - previous for previous, current in zip(rx_times, rx_times[1:])
    ]

    summary: dict[str, object] = {
        "received_packets": len(rx_sequences),
        "first_sequence": min(rx_sequences) if rx_sequences else None,
        "last_sequence": max(rx_sequences) if rx_sequences else None,
        "sequence_gaps": sequence_gaps,
        "rx_gap_events": gap_events,
        "boot_events": boot_count,
        "fault_events": fault_count,
        "inter_arrival_min_us": min(inter_arrival_us) if inter_arrival_us else None,
        "inter_arrival_mean_us": (
            sum(inter_arrival_us) / len(inter_arrival_us)
            if inter_arrival_us
            else None
        ),
        "inter_arrival_p95_us": percentile(inter_arrival_us, 0.95),
        "inter_arrival_p99_us": percentile(inter_arrival_us, 0.99),
        "inter_arrival_max_us": max(inter_arrival_us) if inter_arrival_us else None,
        "rssi_min_dbm": min(rssi_values) if rssi_values else None,
        "rssi_mean_dbm": (
            sum(rssi_values) / len(rssi_values) if rssi_values else None
        ),
        "lqi_min": min(lqi_values) if lqi_values else None,
        "lqi_mean": sum(lqi_values) / len(lqi_values) if lqi_values else None,
    }

    criteria = {
        "min_received": min_received,
        "expected_first_sequence": expected_first_sequence,
        "expected_last_sequence": expected_last_sequence,
        "max_sequence_gaps": max_sequence_gaps,
        "max_rx_gap_events": max_rx_gap_events,
        "max_fault_events": max_fault_events,
        "max_boot_events": max_boot_events,
        "max_inter_arrival_us": max_inter_arrival_us,
    }
    active_criteria = {key: value for key, value in criteria.items() if value is not None}
    if active_criteria:
        failures = []
        if min_received is not None and len(rx_sequences) < min_received:
            failures.append(
                f"received_packets {len(rx_sequences)} < min_received {min_received}"
            )
        if (
            expected_first_sequence is not None
            and summary["first_sequence"] != expected_first_sequence
        ):
            failures.append(
                "first_sequence "
                f"{summary['first_sequence']} != expected {expected_first_sequence}"
            )
        if (
            expected_last_sequence is not None
            and summary["last_sequence"] != expected_last_sequence
        ):
            failures.append(
                "last_sequence "
                f"{summary['last_sequence']} != expected {expected_last_sequence}"
            )
        if max_sequence_gaps is not None and sequence_gaps > max_sequence_gaps:
            failures.append(
                f"sequence_gaps {sequence_gaps} > max_sequence_gaps {max_sequence_gaps}"
            )
        if max_rx_gap_events is not None and gap_events > max_rx_gap_events:
            failures.append(
                f"rx_gap_events {gap_events} > max_rx_gap_events {max_rx_gap_events}"
            )
        if max_fault_events is not None and fault_count > max_fault_events:
            failures.append(
                f"fault_events {fault_count} > max_fault_events {max_fault_events}"
            )
        if max_boot_events is not None and boot_count > max_boot_events:
            failures.append(
                f"boot_events {boot_count} > max_boot_events {max_boot_events}"
            )
        if (
            max_inter_arrival_us is not None
            and summary["inter_arrival_max_us"] is not None
            and summary["inter_arrival_max_us"] > max_inter_arrival_us
        ):
            failures.append(
                "inter_arrival_max_us "
                f"{summary['inter_arrival_max_us']} > max_inter_arrival_us "
                f"{max_inter_arrival_us}"
            )

        summary["criteria"] = active_criteria
        summary["failures"] = failures
        summary["pass"] = not failures

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze OpenRef packet-pair logs")
    parser.add_argument("log", type=Path)
    parser.add_argument("--min-received", type=int)
    parser.add_argument("--expected-first-sequence", type=int)
    parser.add_argument("--expected-last-sequence", type=int)
    parser.add_argument("--max-sequence-gaps", type=int)
    parser.add_argument("--max-rx-gap-events", type=int)
    parser.add_argument("--max-fault-events", type=int)
    parser.add_argument("--max-boot-events", type=int)
    parser.add_argument("--max-inter-arrival-us", type=int)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    for name in (
        "min_received",
        "max_sequence_gaps",
        "max_rx_gap_events",
        "max_fault_events",
        "max_boot_events",
        "max_inter_arrival_us",
    ):
        value = getattr(args, name)
        if value is not None and value < 0:
            parser.error(f"--{name.replace('_', '-')} must be non-negative")

    summary = analyze(
        args.log,
        min_received=args.min_received,
        expected_first_sequence=args.expected_first_sequence,
        expected_last_sequence=args.expected_last_sequence,
        max_sequence_gaps=args.max_sequence_gaps,
        max_rx_gap_events=args.max_rx_gap_events,
        max_fault_events=args.max_fault_events,
        max_boot_events=args.max_boot_events,
        max_inter_arrival_us=args.max_inter_arrival_us,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    if "pass" in summary:
        raise SystemExit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
