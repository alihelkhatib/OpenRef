from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
import re
import statistics
import time

from capture_serial import _load_serial
from openref_autorole_run import (
    DEFAULT_ELF,
    DEFAULT_NM,
    PAYLOAD_SYMBOL,
    ROLE_SYMBOL,
    resolve_named_symbol_address,
)
from railtest_pair_smoke import drain_text, reader, write_command


SCHEDTX_ATTEMPTS_SYMBOL = "openref_app_schedtx_attempts"
ROLE_SCHEDULED_TX = 3

MARKER_RE = re.compile(
    r"\{\{\(openrefSchedTx\)\}(?P<body>(?:\{[^{}]+:[^{}]*\})+)\}\}",
    re.DOTALL,
)
FIELD_RE = re.compile(r"\{(?P<key>[^:{}]+):(?P<value>[^{}]+)\}")


def parse_schedtx_markers(text: str) -> list[dict[str, str]]:
    markers: list[dict[str, str]] = []
    for match in MARKER_RE.finditer(text):
        fields = {
            field.group("key"): field.group("value")
            for field in FIELD_RE.finditer(match.group("body"))
        }
        if fields:
            markers.append(fields)
    return markers


def percentile(values: list[int], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


def summarize_markers(markers: list[dict[str, str]]) -> dict[str, object]:
    queued = [marker for marker in markers if marker.get("Status") == "Queued"]
    started = [marker for marker in markers if marker.get("Status") == "Started"]
    done = [marker for marker in markers if marker.get("Status") == "Done"]
    summary = next((marker for marker in reversed(markers) if marker.get("Status") == "Summary"), None)
    errors = [
        int(marker["LaunchErrorUs"])
        for marker in started
        if "LaunchErrorUs" in marker
    ]
    return {
        "queued": len(queued),
        "started": len(started),
        "done": len(done),
        "summary_attempts": int(summary["Attempts"]) if summary and "Attempts" in summary else None,
        "summary_accepted": int(summary["Accepted"]) if summary and "Accepted" in summary else None,
        "summary_rejected": int(summary["Rejected"]) if summary and "Rejected" in summary else None,
        "launch_error_min_us": min(errors) if errors else None,
        "launch_error_mean_us": statistics.fmean(errors) if errors else None,
        "launch_error_p95_us": percentile(errors, 0.95),
        "launch_error_p99_us": percentile(errors, 0.99),
        "launch_error_max_us": max(errors) if errors else None,
    }


def run_scheduled_tx(
    *,
    port: str,
    output_dir: Path,
    baud: int,
    attempts: int,
    payload_bytes: int,
    rf_path: int | None,
    role_address: int,
    payload_address: int | None,
    attempts_address: int,
    timeout_seconds: float,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = output_dir / f"{run_id}-openref-scheduled-tx-{port.lower()}.log"
    sink: queue.Queue[str] = queue.Queue()

    import threading

    stop = threading.Event()
    with serial.Serial(port, baudrate=baud, timeout=0.1) as handle:
        thread = threading.Thread(
            target=reader,
            args=(handle, log_path, stop, sink),
            daemon=True,
        )
        thread.start()
        time.sleep(0.5)
        write_command(handle, "rx 0")
        if rf_path is not None:
            write_command(handle, f"setRfPath {rf_path}")
        write_command(handle, "resetCounters")
        time.sleep(0.3)

        if payload_address is not None:
            write_command(handle, f"setmemw 0x{payload_address:08x} {payload_bytes}")
        write_command(handle, f"setmemw 0x{attempts_address:08x} {attempts}")
        time.sleep(0.3)
        write_command(handle, f"setmemw 0x{role_address:08x} {ROLE_SCHEDULED_TX}")
        time.sleep(timeout_seconds)
        write_command(handle, f"setmemw 0x{role_address:08x} 0")
        time.sleep(0.5)
        write_command(handle, "status")
        time.sleep(0.5)
        stop.set()
        thread.join(timeout=2)

    text = drain_text(sink)
    markers = parse_schedtx_markers(text)
    timing = summarize_markers(markers)
    passed = bool(
        timing["summary_attempts"] == attempts
        and timing["summary_accepted"] == attempts
        and timing["summary_rejected"] == 0
        and timing["queued"] >= attempts
        and timing["started"] >= attempts
        and timing["done"] >= attempts
    )
    summary = {
        "port": port,
        "attempts": attempts,
        "payload_bytes": payload_bytes,
        "packet_bytes": 18 + payload_bytes,
        "role_address": f"0x{role_address:08x}",
        "payload_address": f"0x{payload_address:08x}" if payload_address is not None else None,
        "attempts_address": f"0x{attempts_address:08x}",
        "timeout_seconds": timeout_seconds,
        "pass": passed,
        "log": str(log_path),
        **timing,
    }
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the OpenRef AutoRole scheduled-TX timing probe."
    )
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--attempts", type=int, default=100)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--role-address", type=lambda value: int(value, 0))
    parser.add_argument("--payload-address", type=lambda value: int(value, 0))
    parser.add_argument("--attempts-address", type=lambda value: int(value, 0))
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    if args.payload_bytes < 0 or args.payload_bytes > 255:
        parser.error("--payload-bytes must be between 0 and 255")

    role_address = args.role_address
    if role_address is None:
        role_address = resolve_named_symbol_address(
            nm_path=args.nm,
            elf_path=args.elf,
            symbol=ROLE_SYMBOL,
        )

    payload_address = args.payload_address
    if payload_address is None:
        try:
            payload_address = resolve_named_symbol_address(
                nm_path=args.nm,
                elf_path=args.elf,
                symbol=PAYLOAD_SYMBOL,
            )
        except ValueError:
            payload_address = None

    attempts_address = args.attempts_address
    if attempts_address is None:
        attempts_address = resolve_named_symbol_address(
            nm_path=args.nm,
            elf_path=args.elf,
            symbol=SCHEDTX_ATTEMPTS_SYMBOL,
        )

    raise SystemExit(
        run_scheduled_tx(
            port=args.port,
            output_dir=args.output_dir,
            baud=args.baud,
            attempts=args.attempts,
            payload_bytes=args.payload_bytes,
            rf_path=args.rf_path,
            role_address=role_address,
            payload_address=payload_address,
            attempts_address=attempts_address,
            timeout_seconds=args.timeout_seconds,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
