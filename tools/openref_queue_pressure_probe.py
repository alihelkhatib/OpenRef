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
from openref_autorole_run import (
    DEFAULT_ELF,
    DEFAULT_NM,
    PAYLOAD_SYMBOL,
    ROLE_SYMBOL,
    resolve_named_symbol_address,
)
from openref_autorx_marker_run import parse_autorx_markers
from railtest_openref_packet_run import (
    HEADER_BYTES,
    build_openref_packet,
    payload_commands,
)
from railtest_pair_smoke import drain_text, reader, write_command


ROLE_RX = 2
STATUS_COUNTERS = ("RxFifoFull", "RxOverflow", "NoRxBuffer", "FrameErrors")
STATUS_COUNTER_RE = re.compile(r"\{(?P<name>RxFifoFull|RxOverflow|NoRxBuffer|FrameErrors):(?P<value>\d+)\}")


def parse_status_counters(text: str) -> dict[str, int]:
    counters = {name: 0 for name in STATUS_COUNTERS}
    for match in STATUS_COUNTER_RE.finditer(text):
        counters[match.group("name")] = int(match.group("value"))
    return counters


def run_queue_pressure_probe(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    packets: int,
    payload_bytes: int,
    command_delay_seconds: float,
    tx_interval_seconds: float,
    rf_path: int | None,
    role_address: int,
    payload_address: int | None,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    rx_log = output_dir / f"{run_id}-openref-queue-pressure-{rx_port.lower()}-rx.log"
    tx_log = output_dir / f"{run_id}-openref-queue-pressure-{tx_port.lower()}-tx.log"

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()
    packet_bytes = HEADER_BYTES + payload_bytes

    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        with serial.Serial(tx_port, baudrate=baud, timeout=0.1) as tx_handle:
            rx_thread = threading.Thread(target=reader, args=(rx_handle, rx_log, stop, rx_sink), daemon=True)
            tx_thread = threading.Thread(target=reader, args=(tx_handle, tx_log, stop, tx_sink), daemon=True)
            rx_thread.start()
            tx_thread.start()
            time.sleep(0.5)

            for handle in (rx_handle, tx_handle):
                write_command(handle, "rx 0")
            time.sleep(0.3)
            if rf_path is not None:
                write_command(rx_handle, f"setRfPath {rf_path}")
                write_command(tx_handle, f"setRfPath {rf_path}")
                time.sleep(0.3)

            write_command(rx_handle, "resetCounters")
            write_command(tx_handle, "resetCounters")
            if payload_address is not None:
                write_command(rx_handle, f"setmemw 0x{payload_address:08x} {payload_bytes}")
            time.sleep(0.3)
            write_command(rx_handle, f"setmemw 0x{role_address:08x} {ROLE_RX}")
            time.sleep(1.0)

            for command in ("setNotifications 1", f"setFixedLength {packet_bytes}"):
                write_command(tx_handle, command)
                time.sleep(command_delay_seconds)

            for sequence in range(1, packets + 1):
                packet = build_openref_packet(
                    source_id=1,
                    destination_id=2,
                    sequence=sequence,
                    timestamp_us=int(time.time_ns() // 1000),
                    payload_bytes=payload_bytes,
                )
                for command in payload_commands(packet):
                    write_command(tx_handle, command)
                    time.sleep(command_delay_seconds)
                write_command(tx_handle, "tx 1")
                time.sleep(tx_interval_seconds)

            time.sleep(2.0)
            write_command(rx_handle, f"setmemw 0x{role_address:08x} 0")
            write_command(rx_handle, "status")
            write_command(tx_handle, "status")
            time.sleep(0.5)
            stop.set()
            rx_thread.join(timeout=2)
            tx_thread.join(timeout=2)

    rx_text = drain_text(rx_sink)
    tx_text = drain_text(tx_sink)
    markers = parse_autorx_markers(rx_text)
    last = markers[-1] if markers else None
    counters = parse_status_counters(rx_text)
    tx_command_overflow = "Input buffer is FULL" in tx_text
    passed = bool(
        last
        and last["rx"] >= packets
        and last["sequence"] == packets
        and last["gaps"] == 0
        and last["faults"] == 0
        and all(counters[name] == 0 for name in STATUS_COUNTERS)
        and not tx_command_overflow
    )
    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "packets": packets,
        "payload_bytes": payload_bytes,
        "packet_bytes": packet_bytes,
        "tx_interval_seconds": tx_interval_seconds,
        "command_delay_seconds": command_delay_seconds,
        "last_rx": last["rx"] if last else 0,
        "last_sequence": last["sequence"] if last else None,
        "last_gaps": last["gaps"] if last else None,
        "last_faults": last["faults"] if last else None,
        "rx_status_counters": counters,
        "tx_command_overflow": tx_command_overflow,
        "role_address": f"0x{role_address:08x}",
        "payload_address": f"0x{payload_address:08x}" if payload_address is not None else None,
        "pass": passed,
        "rx_log": str(rx_log),
        "tx_log": str(tx_log),
    }
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject a valid OpenRef packet burst into AutoRole RX and verify queue health."
    )
    parser.add_argument("--rx-port", required=True)
    parser.add_argument("--tx-port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--packets", type=int, default=50)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--command-delay-seconds", type=float, default=0.12)
    parser.add_argument("--tx-interval-seconds", type=float, default=0.20)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument("--role-address", type=lambda value: int(value, 0))
    parser.add_argument("--payload-address", type=lambda value: int(value, 0))
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument("--output-dir", type=Path, default=Path("firmware/prototype0/fg23/results"))
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    if args.packets < 1:
        parser.error("--packets must be at least 1")
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

    raise SystemExit(
        run_queue_pressure_probe(
            rx_port=args.rx_port,
            tx_port=args.tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            packets=args.packets,
            payload_bytes=args.payload_bytes,
            command_delay_seconds=args.command_delay_seconds,
            tx_interval_seconds=args.tx_interval_seconds,
            rf_path=args.rf_path,
            role_address=role_address,
            payload_address=payload_address,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
