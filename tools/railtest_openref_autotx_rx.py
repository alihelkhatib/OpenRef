from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
import threading
import time

from capture_serial import _load_serial
from railtest_openref_packet_run import (
    HEADER_BYTES,
    DEFAULT_PAYLOAD_BYTES,
    extract_rx_payloads,
    parse_openref_packet,
)
from railtest_pair_smoke import drain_text, reader, write_command


def run_autotx_rx(
    *,
    rx_port: str,
    tx_port: str | None,
    output_dir: Path,
    baud: int,
    expected_packets: int,
    payload_bytes: int,
    duration_seconds: float,
    rf_path: int | None,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    rx_log = output_dir / f"{run_id}-openref-autotx-{rx_port.lower()}-rx.log"
    tx_log = (
        output_dir / f"{run_id}-openref-autotx-{tx_port.lower()}-tx.log"
        if tx_port is not None
        else None
    )

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()

    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        tx_handle_context = (
            serial.Serial(tx_port, baudrate=baud, timeout=0.1)
            if tx_port is not None
            else None
        )
        with tx_handle_context if tx_handle_context is not None else nullcontext():
            rx_thread = threading.Thread(
                target=reader,
                args=(rx_handle, rx_log, stop, rx_sink),
                daemon=True,
            )
            rx_thread.start()
            tx_thread = None
            if tx_handle_context is not None and tx_log is not None:
                tx_thread = threading.Thread(
                    target=reader,
                    args=(tx_handle_context, tx_log, stop, tx_sink),
                    daemon=True,
                )
                tx_thread.start()

            write_command(rx_handle, "rx 0")
            time.sleep(0.2)
            if rf_path is not None:
                write_command(rx_handle, f"setRfPath {rf_path}")
                if tx_handle_context is not None:
                    write_command(tx_handle_context, f"setRfPath {rf_path}")
                time.sleep(0.3)

            packet_bytes = HEADER_BYTES + payload_bytes
            for command in (
                "resetCounters",
                "setNotifications 1",
                f"setFixedLength {packet_bytes}",
                "rx 1",
            ):
                write_command(rx_handle, command)
                time.sleep(0.2)

            if tx_handle_context is not None:
                for command in ("resetCounters", "setNotifications 1"):
                    write_command(tx_handle_context, command)
                    time.sleep(0.2)

            time.sleep(duration_seconds)
            write_command(rx_handle, "status")
            if tx_handle_context is not None:
                write_command(tx_handle_context, "status")
            time.sleep(0.5)
            write_command(rx_handle, "rx 0")
            time.sleep(0.2)

            stop.set()
            rx_thread.join(timeout=2)
            if tx_thread is not None:
                tx_thread.join(timeout=2)

    rx_text = drain_text(rx_sink)
    tx_text = drain_text(tx_sink)
    headers = [
        header
        for payload in extract_rx_payloads(rx_text)
        if (header := parse_openref_packet(payload)) is not None
    ]
    sequences = [header.sequence for header in headers]
    unique_sequences = sorted(set(sequences))
    gap_count = sum(
        1
        for previous, current in zip(unique_sequences, unique_sequences[1:])
        if current != previous + 1
    )

    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "expected_packets": expected_packets,
        "payload_bytes": payload_bytes,
        "packet_bytes": packet_bytes,
        "decoded_openref_packets": len(headers),
        "unique_sequences": len(unique_sequences),
        "first_sequence": unique_sequences[0] if unique_sequences else None,
        "last_sequence": unique_sequences[-1] if unique_sequences else None,
        "gap_count": gap_count,
        "duplicate_count": len(sequences) - len(unique_sequences),
        "pass": len(unique_sequences) >= expected_packets and gap_count == 0,
        "rx_log": str(rx_log),
        "tx_log": str(tx_log) if tx_log is not None else None,
        "tx_autotx_markers": tx_text.count("openrefAutoTx"),
    }

    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if summary["pass"] else 1


class nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, traceback):
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate board-generated OpenRef AutoTX packets with a RAILtest receiver."
    )
    parser.add_argument("--rx-port", required=True)
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--expected-packets", type=int, default=10)
    parser.add_argument("--payload-bytes", type=int, default=DEFAULT_PAYLOAD_BYTES)
    parser.add_argument("--duration-seconds", type=float, default=8.0)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    raise SystemExit(
        run_autotx_rx(
            rx_port=args.rx_port,
            tx_port=args.tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            expected_packets=args.expected_packets,
            payload_bytes=args.payload_bytes,
            duration_seconds=args.duration_seconds,
            rf_path=args.rf_path,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
