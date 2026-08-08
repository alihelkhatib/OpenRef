from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import queue
import re
import struct
import threading
import time

from capture_serial import _load_serial
from railtest_pair_smoke import drain_text, reader, write_command
from railtest_smoke import discover_segger_serial_ports


MAGIC = b"RO"
VERSION = 1
KIND_PING = 1
HEADER_BYTES = 18
DEFAULT_PAYLOAD_BYTES = 60

RX_PACKET_RE = re.compile(r"\{\{\(rxPacket\).*?\{payload:\s*(.*?)\}\}", re.DOTALL)
HEX_BYTE_RE = re.compile(r"0x([0-9a-fA-F]{2})")


@dataclass(frozen=True)
class OpenRefHeader:
    version: int
    kind: int
    source_id: int
    destination_id: int
    sequence: int
    tx_timestamp_us: int
    payload_length: int


def build_openref_packet(
    *,
    source_id: int,
    destination_id: int,
    sequence: int,
    timestamp_us: int,
    payload_bytes: int,
) -> bytes:
    header = struct.pack(
        "<2sBBBBHQH",
        MAGIC,
        VERSION,
        KIND_PING,
        source_id,
        destination_id,
        sequence & 0xFFFF,
        timestamp_us & 0xFFFFFFFFFFFFFFFF,
        payload_bytes,
    )
    payload = bytes(((sequence + index) & 0xFF) for index in range(payload_bytes))
    return header + payload


def parse_openref_packet(packet: bytes) -> OpenRefHeader | None:
    if len(packet) < HEADER_BYTES:
        return None
    magic, version, kind, source, destination, sequence, timestamp, payload_len = struct.unpack(
        "<2sBBBBHQH", packet[:HEADER_BYTES]
    )
    if magic != MAGIC or version != VERSION or kind != KIND_PING:
        return None
    if len(packet) < HEADER_BYTES + payload_len:
        return None
    return OpenRefHeader(
        version=version,
        kind=kind,
        source_id=source,
        destination_id=destination,
        sequence=sequence,
        tx_timestamp_us=timestamp,
        payload_length=payload_len,
    )


def extract_rx_payloads(text: str) -> list[bytes]:
    payloads: list[bytes] = []
    for match in RX_PACKET_RE.finditer(text):
        payloads.append(bytes(int(value, 16) for value in HEX_BYTE_RE.findall(match.group(1))))
    return payloads


def payload_commands(packet: bytes, *, chunk_size: int = 16) -> list[str]:
    commands = [f"setTxLength {len(packet)}"]
    for offset in range(0, len(packet), chunk_size):
        chunk = packet[offset : offset + chunk_size]
        values = " ".join(str(byte) for byte in chunk)
        commands.append(f"setTxPayloadQuiet {offset} {values}")
    return commands


def run_openref_packet_run(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    packets: int,
    payload_bytes: int,
    interval_seconds: float,
    command_delay_seconds: float,
    settle_seconds: float,
    rf_path: int | None,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    rx_log = output_dir / f"{run_id}-railtest-openref-{rx_port.lower()}-rx.log"
    tx_log = output_dir / f"{run_id}-railtest-openref-{tx_port.lower()}-tx.log"

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()

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

            for handle in (rx_handle, tx_handle):
                write_command(handle, "rx 0")
            time.sleep(0.3)

            if rf_path is not None:
                for handle in (rx_handle, tx_handle):
                    write_command(handle, f"setRfPath {rf_path}")
                time.sleep(0.3)

            for command in ("resetCounters", "setNotifications 1", "rx 1"):
                if command == "rx 1":
                    write_command(rx_handle, f"setFixedLength {HEADER_BYTES + payload_bytes}")
                    time.sleep(command_delay_seconds)
                write_command(rx_handle, command)
                time.sleep(command_delay_seconds)

            for command in (
                "resetCounters",
                "setNotifications 1",
                f"setFixedLength {HEADER_BYTES + payload_bytes}",
            ):
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
                time.sleep(interval_seconds)

            time.sleep(settle_seconds)
            write_command(rx_handle, "status")
            write_command(tx_handle, "status")
            time.sleep(0.5)
            write_command(rx_handle, "rx 0")
            time.sleep(0.2)

            stop.set()
            rx_thread.join(timeout=2)
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
    missing_sequences = [
        sequence for sequence in range(1, packets + 1) if sequence not in unique_sequences
    ]
    duplicate_count = len(sequences) - len(unique_sequences)

    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "requested_packets": packets,
        "payload_bytes": payload_bytes,
        "packet_bytes": HEADER_BYTES + payload_bytes,
        "decoded_openref_packets": len(headers),
        "unique_sequences": len(unique_sequences),
        "first_sequence": unique_sequences[0] if unique_sequences else None,
        "last_sequence": unique_sequences[-1] if unique_sequences else None,
        "missing_sequences": missing_sequences,
        "duplicate_count": duplicate_count,
        "pass": len(missing_sequences) == 0,
        "rx_log": str(rx_log),
        "tx_log": str(tx_log),
    }

    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if summary["pass"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transmit OpenRef prototype packets through two RAILtest boards."
    )
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--packets", type=int, default=25)
    parser.add_argument("--payload-bytes", type=int, default=DEFAULT_PAYLOAD_BYTES)
    parser.add_argument("--interval-seconds", type=float, default=0.25)
    parser.add_argument("--command-delay-seconds", type=float, default=0.12)
    parser.add_argument("--settle-seconds", type=float, default=1.0)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    ports = discover_segger_serial_ports()
    rx_port = args.rx_port or (ports[0] if len(ports) >= 1 else None)
    tx_port = args.tx_port or (ports[1] if len(ports) >= 2 else None)
    if rx_port is None or tx_port is None or rx_port == tx_port:
        print(
            "FAIL: provide two distinct ports with --rx-port and --tx-port, "
            f"or connect two SEGGER serial devices. Found: {', '.join(ports) or 'none'}"
        )
        raise SystemExit(1)

    raise SystemExit(
        run_openref_packet_run(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            packets=args.packets,
            payload_bytes=args.payload_bytes,
            interval_seconds=args.interval_seconds,
            command_delay_seconds=args.command_delay_seconds,
            settle_seconds=args.settle_seconds,
            rf_path=args.rf_path,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
