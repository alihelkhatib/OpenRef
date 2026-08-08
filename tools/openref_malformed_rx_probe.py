from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
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
PARSE_FAIL_TEXT = "Status:ParseFail"


def malformed_packet(*, payload_bytes: int, pattern: int = 0xA5) -> bytes:
    packet_bytes = HEADER_BYTES + payload_bytes
    data = bytearray((pattern + index) & 0xFF for index in range(packet_bytes))
    data[0] = 0x00
    data[1] = 0x00
    return bytes(data)


def run_malformed_probe(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    malformed_packets: int,
    recovery_packets: int,
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
    rx_log = output_dir / f"{run_id}-openref-malformed-{rx_port.lower()}-rx.log"
    tx_log = output_dir / f"{run_id}-openref-malformed-{tx_port.lower()}-tx.log"

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()
    packet_bytes = HEADER_BYTES + payload_bytes

    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        with serial.Serial(tx_port, baudrate=baud, timeout=0.1) as tx_handle:
            rx_thread = threading.Thread(
                target=reader,
                args=(rx_handle, rx_log, stop, rx_sink),
                daemon=True,
            )
            tx_thread = threading.Thread(
                target=reader,
                args=(tx_handle, tx_log, stop, tx_sink),
                daemon=True,
            )
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

            for command in (
                "setNotifications 1",
                f"setFixedLength {packet_bytes}",
            ):
                write_command(tx_handle, command)
                time.sleep(command_delay_seconds)

            bad = malformed_packet(payload_bytes=payload_bytes)
            for _ in range(malformed_packets):
                for command in payload_commands(bad):
                    write_command(tx_handle, command)
                    time.sleep(command_delay_seconds)
                write_command(tx_handle, "tx 1")
                time.sleep(tx_interval_seconds)

            for sequence in range(1, recovery_packets + 1):
                good = build_openref_packet(
                    source_id=1,
                    destination_id=2,
                    sequence=sequence,
                    timestamp_us=int(time.time_ns() // 1000),
                    payload_bytes=payload_bytes,
                )
                for command in payload_commands(good):
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
    parse_fail_count = rx_text.count(PARSE_FAIL_TEXT)
    markers = parse_autorx_markers(rx_text)
    last = markers[-1] if markers else None
    passed = bool(
        parse_fail_count >= malformed_packets
        and last
        and last["rx"] >= recovery_packets
        and last["faults"] >= malformed_packets
    )
    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "malformed_packets": malformed_packets,
        "recovery_packets": recovery_packets,
        "payload_bytes": payload_bytes,
        "packet_bytes": packet_bytes,
        "parse_fail_count": parse_fail_count,
        "last_rx": last["rx"] if last else 0,
        "last_sequence": last["sequence"] if last else None,
        "last_gaps": last["gaps"] if last else None,
        "last_faults": last["faults"] if last else None,
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
        description="Inject malformed packets into OpenRef AutoRole RX and verify recovery."
    )
    parser.add_argument("--rx-port", required=True)
    parser.add_argument("--tx-port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--malformed-packets", type=int, default=10)
    parser.add_argument("--recovery-packets", type=int, default=25)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--command-delay-seconds", type=float, default=0.08)
    parser.add_argument("--tx-interval-seconds", type=float, default=0.15)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument("--role-address", type=lambda value: int(value, 0))
    parser.add_argument("--payload-address", type=lambda value: int(value, 0))
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    if args.malformed_packets < 1:
        parser.error("--malformed-packets must be at least 1")
    if args.recovery_packets < 1:
        parser.error("--recovery-packets must be at least 1")
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
        run_malformed_probe(
            rx_port=args.rx_port,
            tx_port=args.tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            malformed_packets=args.malformed_packets,
            recovery_packets=args.recovery_packets,
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
