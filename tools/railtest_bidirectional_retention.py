from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from railtest_packet_run import run_packet_check


def _direction_passes(summary: dict[str, Any], packets: int) -> bool:
    return (
        summary.get("transmitted_packets") == packets
        and summary.get("rx_count") == packets
        and summary.get("rx_crc_drop") in (0, None)
        and summary.get("tx_failed_packets") in (0, None)
    )


def _load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_direction(
    *,
    label: str,
    rx_port: str,
    tx_port: str,
    output_root: Path,
    baud: int,
    packets: int,
    payload_bytes: int,
    tx_delay_ms: int | None,
    settle_seconds: float,
    rf_path: int,
) -> dict[str, Any]:
    output_dir = output_root / label
    summary_json = output_dir / f"{label}-summary.json"
    returncode = run_packet_check(
        rx_port=rx_port,
        tx_port=tx_port,
        output_dir=output_dir,
        baud=baud,
        packets=packets,
        payload_bytes=payload_bytes,
        tx_delay_ms=tx_delay_ms,
        settle_seconds=settle_seconds,
        rf_path=rf_path,
        summary_json=summary_json,
    )
    summary = _load_summary(summary_json) if summary_json.exists() else {}
    failures = []
    if returncode != 0:
        failures.append(f"packet check exited {returncode}")
    if not _direction_passes(summary, packets):
        failures.append(
            "packet counters did not match requested count with zero drops/failures"
        )
    return {
        "label": label,
        "rx_port": rx_port,
        "tx_port": tx_port,
        "returncode": returncode,
        "pass": not failures,
        "failures": failures,
        "summary_json": str(summary_json),
        "summary": summary,
    }


def run_bidirectional_retention(
    *,
    rx_port: str,
    tx_port: str,
    output_root: Path,
    baud: int = 115200,
    packets: int = 200,
    payload_bytes: int = 60,
    tx_delay_ms: int | None = 20,
    settle_seconds: float = 12.0,
    rf_path: int = 0,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    directions = [
        (rx_port, tx_port, f"{timestamp}-{tx_port}-to-{rx_port}"),
        (tx_port, rx_port, f"{timestamp}-{rx_port}-to-{tx_port}"),
    ]
    results = [
        _run_direction(
            label=label,
            rx_port=direction_rx,
            tx_port=direction_tx,
            output_root=output_root,
            baud=baud,
            packets=packets,
            payload_bytes=payload_bytes,
            tx_delay_ms=tx_delay_ms,
            settle_seconds=settle_seconds,
            rf_path=rf_path,
        )
        for direction_rx, direction_tx, label in directions
    ]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pass": all(item["pass"] for item in results),
        "rf_path": rf_path,
        "packets": packets,
        "payload_bytes": payload_bytes,
        "tx_delay_ms": tx_delay_ms,
        "settle_seconds": settle_seconds,
        "directions": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a bidirectional FG23 RAILtest packet-retention check."
    )
    parser.add_argument("--rx-port", default="COM8")
    parser.add_argument("--tx-port", default="COM10")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--packets", type=int, default=200)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--tx-delay-ms", type=int, default=20)
    parser.add_argument("--settle-seconds", type=float, default=12.0)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("firmware/prototype0/fg23/results/retention-packet-run"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    report = run_bidirectional_retention(
        rx_port=args.rx_port,
        tx_port=args.tx_port,
        output_root=args.output_root,
        baud=args.baud,
        packets=args.packets,
        payload_bytes=args.payload_bytes,
        tx_delay_ms=args.tx_delay_ms,
        settle_seconds=args.settle_seconds,
        rf_path=args.rf_path,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.summary_json is not None:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
