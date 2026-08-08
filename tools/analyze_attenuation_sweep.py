from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"{path} must contain a JSON object or list of objects")


def _number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_number(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _step_label(summary: dict[str, Any], fallback: str) -> str:
    for key in ("attenuation_db", "attenuation", "step", "label"):
        value = summary.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


def summarize_step(summary: dict[str, Any], *, fallback_label: str) -> dict[str, Any]:
    transmitted = _int_number(summary.get("transmitted_packets"))
    rx_count = _int_number(summary.get("rx_count"))
    requested = _int_number(summary.get("requested_packets"))
    crc_drop = _int_number(summary.get("rx_crc_drop"))
    denominator = transmitted or requested or 0
    delivery_ratio = _number(summary.get("delivery_ratio"))
    if delivery_ratio is None and denominator > 0 and rx_count is not None:
        delivery_ratio = rx_count / denominator

    packet_error_rate = (
        1.0 - delivery_ratio
        if delivery_ratio is not None
        else None
    )
    lost_packets = (
        denominator - rx_count
        if denominator > 0 and rx_count is not None
        else None
    )

    return {
        "label": _step_label(summary, fallback_label),
        "rx_port": summary.get("rx_port"),
        "tx_port": summary.get("tx_port"),
        "rf_path": summary.get("rf_path"),
        "tx_power_dbm": summary.get("tx_power_dbm"),
        "actual_tx_power_dbm": summary.get("actual_tx_power_dbm"),
        "payload_bytes": summary.get("payload_bytes"),
        "requested_packets": requested,
        "transmitted_packets": transmitted,
        "rx_count": rx_count,
        "lost_packets": lost_packets,
        "rx_crc_drop": crc_drop,
        "delivery_ratio": delivery_ratio,
        "packet_error_rate": packet_error_rate,
    }


def analyze(
    paths: list[str | Path],
    *,
    labels: list[str] | None = None,
    min_steps: int = 2,
    require_degraded_step: bool = True,
    min_packet_error_rate: float = 0.01,
) -> dict[str, Any]:
    loaded: list[dict[str, Any]] = []
    for path in paths:
        loaded.extend(_load_json(Path(path)))

    if labels is not None and len(labels) != len(loaded):
        raise ValueError("--labels count must match the number of loaded summaries")

    steps = [
        summarize_step(
            summary,
            fallback_label=(labels[index] if labels is not None else f"step-{index + 1}"),
        )
        for index, summary in enumerate(loaded)
    ]
    valid_steps = [
        step
        for step in steps
        if step["transmitted_packets"] not in (None, 0) and step["rx_count"] is not None
    ]
    degraded_steps = [
        step
        for step in valid_steps
        if step["packet_error_rate"] is not None
        and step["packet_error_rate"] >= min_packet_error_rate
    ]
    worst_step = max(
        valid_steps,
        key=lambda step: step["packet_error_rate"] or 0.0,
        default=None,
    )

    passed = len(valid_steps) >= min_steps and (
        bool(degraded_steps) if require_degraded_step else True
    )

    return {
        "input_files": [str(path) for path in paths],
        "steps": steps,
        "valid_steps": len(valid_steps),
        "min_steps": min_steps,
        "require_degraded_step": require_degraded_step,
        "min_packet_error_rate": min_packet_error_rate,
        "degraded_steps": len(degraded_steps),
        "worst_step": worst_step,
        "pass": passed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze OpenRef E0-05 controlled attenuation packet summaries."
    )
    parser.add_argument("summary_json", nargs="+", type=Path)
    parser.add_argument("--labels", nargs="+")
    parser.add_argument("--min-steps", type=int, default=2)
    parser.add_argument("--min-packet-error-rate", type=float, default=0.01)
    parser.add_argument(
        "--allow-no-degraded-step",
        action="store_true",
        help="Pass with enough valid steps even if every step has zero packet loss.",
    )
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if args.min_steps < 1:
        parser.error("--min-steps must be at least 1")
    if args.min_packet_error_rate < 0 or args.min_packet_error_rate > 1:
        parser.error("--min-packet-error-rate must be between 0 and 1")

    summary = analyze(
        args.summary_json,
        labels=args.labels,
        min_steps=args.min_steps,
        require_degraded_step=not args.allow_no_degraded_step,
        min_packet_error_rate=args.min_packet_error_rate,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")

    raise SystemExit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
