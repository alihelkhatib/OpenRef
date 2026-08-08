from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
import threading
import time

from capture_serial import _load_serial
from railtest_pair_smoke import drain_text, reader, write_command
from railtest_packet_run import parse_last_event_fields
from railtest_smoke import discover_segger_serial_ports


def run_probe(
    *,
    port: str,
    output_dir: Path,
    baud: int,
    count: int,
    relative_delay_us: int,
    spacing_seconds: float,
    rf_path: int | None,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y%m%d")
    log_path = output_dir / f"{date}-railtest-scheduled-tx.log"
    sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()

    with serial.Serial(port, baudrate=baud, timeout=0.1) as handle:
        thread = threading.Thread(
            target=reader,
            args=(handle, log_path, stop, sink),
            daemon=True,
        )
        thread.start()
        write_command(handle, "rx 0")
        time.sleep(0.2)
        if rf_path is not None:
            write_command(handle, f"setRfPath {rf_path}")
            time.sleep(0.2)
        write_command(handle, "resetCounters")
        time.sleep(0.2)
        write_command(handle, "setNotifications 1")
        time.sleep(0.2)

        for _ in range(count):
            write_command(handle, f"txAt {relative_delay_us} rel")
            time.sleep(spacing_seconds)

        write_command(handle, "status")
        time.sleep(0.5)
        stop.set()
        thread.join(timeout=2)

    text = drain_text(sink)
    tx_end_count = text.count("{{(txEnd)}")
    status = parse_last_event_fields(text, "status")
    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "port": port,
        "rf_path": rf_path,
        "requested_scheduled_tx": count,
        "relative_delay_us": relative_delay_us,
        "tx_end_count": tx_end_count,
        "user_tx_count": int(status.get("UserTxCount", "0")),
        "user_tx_started": int(status.get("UserTxStarted", "0")),
        "user_tx_aborted": int(status.get("UserTxAborted", "0")),
        "user_tx_blocked": int(status.get("UserTxBlocked", "0")),
        "user_tx_underflow": int(status.get("UserTxUnderflow", "0")),
        "log": str(log_path),
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(rendered + "\n", encoding="utf-8")

    return 0 if tx_end_count == count and summary["user_tx_count"] == count else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe RAILtest scheduled TX.")
    parser.add_argument("--port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--relative-delay-us", type=int, default=50000)
    parser.add_argument("--spacing-seconds", type=float, default=0.15)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    ports = discover_segger_serial_ports()
    port = args.port or (ports[0] if ports else None)
    if port is None:
        print("FAIL: no SEGGER serial port found")
        raise SystemExit(1)

    raise SystemExit(
        run_probe(
            port=port,
            output_dir=args.output_dir,
            baud=args.baud,
            count=args.count,
            relative_delay_us=args.relative_delay_us,
            spacing_seconds=args.spacing_seconds,
            rf_path=args.rf_path,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
