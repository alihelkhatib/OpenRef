from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, replace
from itertools import product
from pathlib import Path

from .capacity import estimate_capacity
from .run import run_scenario
from .scenario import Scenario, load_scenario


DEFAULT_FRAME_DURATIONS_MS = (10.0, 20.0)
DEFAULT_ENCODED_BITRATES_BPS = (16_000, 24_000, 32_000)
DEFAULT_RADIO_BITRATES_BPS = (250_000, 500_000, 1_000_000)
DEFAULT_SLOT_SPACINGS_US = (1_000, 1_500, 2_000, 2_500, 3_000)
DEFAULT_MAX_UTILIZATION = 0.75
DEFAULT_MIN_DELIVERY_RATIO = 0.999

CSV_FIELDS = [
    "feasible",
    "scenario_name",
    "frame_duration_ms",
    "encoded_bitrate_bps",
    "radio_bitrate_bps",
    "slot_spacing_us",
    "payload_bytes",
    "voice_airtime_us",
    "heartbeat_airtime_us",
    "slot_guard_us",
    "schedule_span_us",
    "scheduled_channel_utilization",
    "delivery_ratio",
    "mean_latency_us",
    "p95_latency_us",
    "p99_latency_us",
    "max_latency_us",
    "collided",
    "randomly_lost",
    "queue_overflows",
    "audio_deadline_misses",
    "max_queue_depth",
]


@dataclass(frozen=True)
class SweepResult:
    feasible: bool
    scenario_name: str
    frame_duration_ms: float
    encoded_bitrate_bps: int
    radio_bitrate_bps: int
    slot_spacing_us: int
    payload_bytes: int
    voice_airtime_us: int
    heartbeat_airtime_us: int
    slot_guard_us: int
    schedule_span_us: int
    scheduled_channel_utilization: float
    delivery_ratio: float | None
    mean_latency_us: float | None
    p95_latency_us: float | None
    p99_latency_us: float | None
    max_latency_us: int | None
    collided: int
    randomly_lost: int
    queue_overflows: int
    audio_deadline_misses: int
    max_queue_depth: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def parse_float_values(raw: str) -> tuple[float, ...]:
    values = tuple(float(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one value is required")
    return values


def parse_int_values(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one value is required")
    return values


def _variant_name(
    base_name: str,
    frame_duration_ms: float,
    encoded_bitrate_bps: int,
    radio_bitrate_bps: int,
    slot_spacing_us: int,
) -> str:
    frame_label = f"{frame_duration_ms:g}".replace(".", "p")
    return (
        f"{base_name}-f{frame_label}ms-c{encoded_bitrate_bps}"
        f"-r{radio_bitrate_bps}-s{slot_spacing_us}"
    )


def _variant_scenario(
    base: Scenario,
    frame_duration_ms: float,
    encoded_bitrate_bps: int,
    radio_bitrate_bps: int,
    slot_spacing_us: int,
) -> Scenario:
    return replace(
        base,
        name=_variant_name(
            base.name,
            frame_duration_ms,
            encoded_bitrate_bps,
            radio_bitrate_bps,
            slot_spacing_us,
        ),
        frame_duration_ms=frame_duration_ms,
        encoded_bitrate_bps=encoded_bitrate_bps,
        radio_bitrate_bps=radio_bitrate_bps,
        slot_spacing_us=slot_spacing_us,
    )


def _is_feasible(
    scenario: Scenario,
    summary: dict[str, object],
    *,
    max_utilization: float,
    min_delivery_ratio: float,
) -> bool:
    delivery_ratio = summary["delivery_ratio"]
    p95_latency_us = summary["p95_latency_us"]
    capacity = estimate_capacity(scenario)
    return (
        isinstance(delivery_ratio, float)
        and delivery_ratio >= min_delivery_ratio
        and int(summary["collided"]) == 0
        and int(summary["queue_overflows"]) == 0
        and int(summary["audio_deadline_misses"]) == 0
        and capacity.scheduled_channel_utilization <= max_utilization
        and capacity.schedule_span_us <= scenario.frame_interval_us
        and (
            p95_latency_us is None
            or float(p95_latency_us) <= scenario.audio_deadline_us
        )
    )


def _result_from_summary(
    scenario: Scenario,
    summary: dict[str, object],
    *,
    max_utilization: float,
    min_delivery_ratio: float,
) -> SweepResult:
    capacity = estimate_capacity(scenario)
    return SweepResult(
        feasible=_is_feasible(
            scenario,
            summary,
            max_utilization=max_utilization,
            min_delivery_ratio=min_delivery_ratio,
        ),
        scenario_name=scenario.name,
        frame_duration_ms=scenario.frame_duration_ms,
        encoded_bitrate_bps=scenario.encoded_bitrate_bps,
        radio_bitrate_bps=scenario.radio_bitrate_bps,
        slot_spacing_us=scenario.slot_spacing_us,
        payload_bytes=scenario.payload_bytes,
        voice_airtime_us=capacity.voice_airtime_us,
        heartbeat_airtime_us=capacity.heartbeat_airtime_us,
        slot_guard_us=capacity.slot_guard_us,
        schedule_span_us=capacity.schedule_span_us,
        scheduled_channel_utilization=capacity.scheduled_channel_utilization,
        delivery_ratio=summary["delivery_ratio"],
        mean_latency_us=summary["mean_latency_us"],
        p95_latency_us=summary["p95_latency_us"],
        p99_latency_us=summary["p99_latency_us"],
        max_latency_us=summary["max_latency_us"],
        collided=int(summary["collided"]),
        randomly_lost=int(summary["randomly_lost"]),
        queue_overflows=int(summary["queue_overflows"]),
        audio_deadline_misses=int(summary["audio_deadline_misses"]),
        max_queue_depth=int(summary["max_queue_depth"]),
    )


def _rank_key(result: SweepResult) -> tuple[object, ...]:
    p95_latency_us = result.p95_latency_us
    return (
        not result.feasible,
        p95_latency_us if p95_latency_us is not None else float("inf"),
        result.scheduled_channel_utilization,
        result.radio_bitrate_bps,
        result.encoded_bitrate_bps,
        result.slot_spacing_us,
    )


def sweep_scenario(
    base: Scenario,
    *,
    frame_durations_ms: tuple[float, ...] = DEFAULT_FRAME_DURATIONS_MS,
    encoded_bitrates_bps: tuple[int, ...] = DEFAULT_ENCODED_BITRATES_BPS,
    radio_bitrates_bps: tuple[int, ...] = DEFAULT_RADIO_BITRATES_BPS,
    slot_spacings_us: tuple[int, ...] = DEFAULT_SLOT_SPACINGS_US,
    max_utilization: float = DEFAULT_MAX_UTILIZATION,
    min_delivery_ratio: float = DEFAULT_MIN_DELIVERY_RATIO,
) -> list[SweepResult]:
    results: list[SweepResult] = []
    for frame_ms, codec_bps, radio_bps, slot_us in product(
        frame_durations_ms,
        encoded_bitrates_bps,
        radio_bitrates_bps,
        slot_spacings_us,
    ):
        scenario = _variant_scenario(base, frame_ms, codec_bps, radio_bps, slot_us)
        _, summary = run_scenario(scenario)
        results.append(
            _result_from_summary(
                scenario,
                summary,
                max_utilization=max_utilization,
                min_delivery_ratio=min_delivery_ratio,
            )
        )
    return sorted(results, key=_rank_key)


def write_sweep_csv(results: list[SweepResult], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(result.as_dict())


def _format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value * 100:.1f}%"


def _format_ms(value_us: float | int | None) -> str:
    if value_us is None:
        return ""
    return f"{float(value_us) / 1_000:.1f}"


def format_sweep_markdown(
    results: list[SweepResult],
    *,
    limit: int | None = None,
) -> str:
    selected = results[:limit] if limit is not None else results
    lines = [
        "| ok | frame_ms | codec_kbps | radio_kbps | slot_us | util | guard_us | p95_ms | delivery | collisions | deadline_misses |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in selected:
        lines.append(
            "| "
            f"{'yes' if result.feasible else 'no'} | "
            f"{result.frame_duration_ms:g} | "
            f"{result.encoded_bitrate_bps // 1_000} | "
            f"{result.radio_bitrate_bps // 1_000} | "
            f"{result.slot_spacing_us} | "
            f"{_format_percent(result.scheduled_channel_utilization)} | "
            f"{result.slot_guard_us} | "
            f"{_format_ms(result.p95_latency_us)} | "
            f"{_format_percent(result.delivery_ratio)} | "
            f"{result.collided} | "
            f"{result.audio_deadline_misses} |"
        )
    return "\n".join(lines)


def write_sweep_markdown(
    results: list[SweepResult],
    path: str | Path,
    *,
    limit: int | None = None,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_sweep_markdown(results, limit=limit) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sweep OpenRef simulator architecture parameters"
    )
    parser.add_argument("scenario", type=Path)
    parser.add_argument(
        "--frame-ms",
        type=parse_float_values,
        default=DEFAULT_FRAME_DURATIONS_MS,
        help="Comma-separated audio frame durations in milliseconds",
    )
    parser.add_argument(
        "--codec-bps",
        type=parse_int_values,
        default=DEFAULT_ENCODED_BITRATES_BPS,
        help="Comma-separated encoded voice bitrates in bits per second",
    )
    parser.add_argument(
        "--radio-bps",
        type=parse_int_values,
        default=DEFAULT_RADIO_BITRATES_BPS,
        help="Comma-separated radio bitrates in bits per second",
    )
    parser.add_argument(
        "--slot-us",
        type=parse_int_values,
        default=DEFAULT_SLOT_SPACINGS_US,
        help="Comma-separated per-node slot spacing values in microseconds",
    )
    parser.add_argument("--max-utilization", type=float, default=DEFAULT_MAX_UTILIZATION)
    parser.add_argument(
        "--min-delivery-ratio",
        type=float,
        default=DEFAULT_MIN_DELIVERY_RATIO,
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    base = load_scenario(args.scenario)
    results = sweep_scenario(
        base,
        frame_durations_ms=args.frame_ms,
        encoded_bitrates_bps=args.codec_bps,
        radio_bitrates_bps=args.radio_bps,
        slot_spacings_us=args.slot_us,
        max_utilization=args.max_utilization,
        min_delivery_ratio=args.min_delivery_ratio,
    )

    if args.csv is not None:
        write_sweep_csv(results, args.csv)
    if args.markdown is not None:
        write_sweep_markdown(results, args.markdown, limit=args.limit)

    feasible = sum(result.feasible for result in results)
    print(
        f"Swept {len(results)} cases from {base.name}; "
        f"{feasible} met the screening criteria."
    )
    print(format_sweep_markdown(results, limit=args.limit))
    if args.csv is not None:
        print(f"CSV: {args.csv}")
    if args.markdown is not None:
        print(f"Markdown: {args.markdown}")


if __name__ == "__main__":
    main()
