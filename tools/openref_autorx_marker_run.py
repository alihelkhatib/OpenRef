from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
import re
import threading
import time

from capture_serial import _load_serial
from railtest_pair_smoke import drain_text, reader, write_command


AUTORX_RE = re.compile(
    r"\{\{\(openrefAutoRx\)\}\{Rx:(?P<rx>\d+)\}\{Sequence:(?P<sequence>\d+)\}"
    r"\{Gaps:(?P<gaps>\d+)\}\{Faults:(?P<faults>\d+)\}"
)


def parse_autorx_markers(text: str) -> list[dict[str, int]]:
    markers = []
    for match in AUTORX_RE.finditer(text):
        markers.append({key: int(value) for key, value in match.groupdict().items()})
    return markers


def run_autorx_marker_capture(
    *,
    rx_port: str,
    tx_port: str | None,
    output_dir: Path,
    baud: int,
    duration_seconds: float,
    expected_rx: int,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    rx_log = output_dir / f"{run_id}-openref-autorx-{rx_port.lower()}-rx.log"
    tx_log = (
        output_dir / f"{run_id}-openref-autorx-{tx_port.lower()}-tx.log"
        if tx_port is not None
        else None
    )

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()

    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        tx_handle = (
            serial.Serial(tx_port, baudrate=baud, timeout=0.1)
            if tx_port is not None
            else None
        )
        try:
            rx_thread = threading.Thread(
                target=reader,
                args=(rx_handle, rx_log, stop, rx_sink),
                daemon=True,
            )
            rx_thread.start()
            tx_thread = None
            if tx_handle is not None and tx_log is not None:
                tx_thread = threading.Thread(
                    target=reader,
                    args=(tx_handle, tx_log, stop, tx_sink),
                    daemon=True,
                )
                tx_thread.start()

            time.sleep(duration_seconds)
            if tx_handle is not None:
                write_command(tx_handle, "status")
            time.sleep(0.5)
        finally:
            stop.set()
            rx_thread.join(timeout=2)
            if tx_thread is not None:
                tx_thread.join(timeout=2)
            if tx_handle is not None:
                tx_handle.close()

    rx_text = drain_text(rx_sink)
    tx_text = drain_text(tx_sink)
    markers = parse_autorx_markers(rx_text)
    last = markers[-1] if markers else None
    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "duration_seconds": duration_seconds,
        "expected_rx": expected_rx,
        "marker_count": len(markers),
        "last_rx": last["rx"] if last else 0,
        "last_sequence": last["sequence"] if last else None,
        "last_gaps": last["gaps"] if last else None,
        "last_faults": last["faults"] if last else None,
        "pass": bool(
            last
            and last["rx"] >= expected_rx
            and last["gaps"] == 0
            and last["faults"] == 0
        ),
        "rx_configured": "Status:Configured" in rx_text,
        "tx_autotx_markers": tx_text.count("openrefAutoTx"),
        "rx_log": str(rx_log),
        "tx_log": str(tx_log) if tx_log is not None else None,
    }
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if summary["pass"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture board-side OpenRef AutoRX counters from serial markers."
    )
    parser.add_argument("--rx-port", required=True)
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration-seconds", type=float, default=30.0)
    parser.add_argument("--expected-rx", type=int, default=50)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    raise SystemExit(
        run_autorx_marker_capture(
            rx_port=args.rx_port,
            tx_port=args.tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            duration_seconds=args.duration_seconds,
            expected_rx=args.expected_rx,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
