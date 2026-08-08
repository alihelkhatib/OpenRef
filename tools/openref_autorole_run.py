from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
import re
import subprocess
import threading
import time

from capture_serial import _load_serial
from openref_autorx_marker_run import parse_autorx_markers
from railtest_pair_smoke import drain_text, reader, write_command


DEFAULT_ELF = Path(
    r"C:\Users\aliel\SimplicityStudio\v6_workspace\rail_soc_railtest"
    r"\cmake_gcc\build\base\rail_soc_railtest.out"
)
DEFAULT_NM = Path(
    r"C:\Users\aliel\.silabs\slt\installs\conan\p\gcc-a999d2e027337f"
    r"\p\bin\arm-none-eabi-nm.exe"
)
ROLE_SYMBOL = "openref_app_role"
PAYLOAD_SYMBOL = "openref_app_payload_bytes"
ROLE_TX = 1
ROLE_RX = 2


def parse_nm_symbol_address(nm_output: str, symbol: str = ROLE_SYMBOL) -> int:
    pattern = re.compile(rf"^([0-9a-fA-F]+)\s+[A-Za-z]\s+{re.escape(symbol)}$", re.MULTILINE)
    match = pattern.search(nm_output)
    if match is None:
        raise ValueError(f"symbol not found: {symbol}")
    return int(match.group(1), 16)


def resolve_symbol_address(*, nm_path: Path, elf_path: Path) -> int:
    return resolve_named_symbol_address(
        nm_path=nm_path,
        elf_path=elf_path,
        symbol=ROLE_SYMBOL,
    )


def resolve_named_symbol_address(*, nm_path: Path, elf_path: Path, symbol: str) -> int:
    result = subprocess.run(
        [str(nm_path), "-g", str(elf_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    return parse_nm_symbol_address(result.stdout, symbol=symbol)


def run_autorole(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    duration_seconds: float,
    expected_rx: int,
    role_address: int,
    payload_address: int | None,
    payload_bytes: int,
    rf_path: int | None,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    rx_log = output_dir / f"{run_id}-openref-autorole-{rx_port.lower()}-rx.log"
    tx_log = output_dir / f"{run_id}-openref-autorole-{tx_port.lower()}-tx.log"

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

            time.sleep(0.5)
            for handle in (rx_handle, tx_handle):
                write_command(handle, "rx 0")
            time.sleep(0.3)

            if rf_path is not None:
                write_command(rx_handle, f"setRfPath {rf_path}")
                write_command(tx_handle, f"setRfPath {rf_path}")
                time.sleep(0.3)

            for handle in (rx_handle, tx_handle):
                write_command(handle, "resetCounters")
            time.sleep(0.3)

            if payload_address is not None:
                for handle in (rx_handle, tx_handle):
                    write_command(handle, f"setmemw 0x{payload_address:08x} {payload_bytes}")
                time.sleep(0.3)

            write_command(rx_handle, f"setmemw 0x{role_address:08x} {ROLE_RX}")
            time.sleep(0.3)
            write_command(tx_handle, f"setmemw 0x{role_address:08x} {ROLE_TX}")
            time.sleep(duration_seconds)

            write_command(rx_handle, f"setmemw 0x{role_address:08x} 0")
            write_command(tx_handle, f"setmemw 0x{role_address:08x} 0")
            time.sleep(0.5)
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
    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "duration_seconds": duration_seconds,
        "expected_rx": expected_rx,
        "role_address": f"0x{role_address:08x}",
        "payload_address": f"0x{payload_address:08x}" if payload_address is not None else None,
        "payload_bytes": payload_bytes,
        "packet_bytes": 18 + payload_bytes,
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
        "rx_role_markers": rx_text.count("openrefRole"),
        "tx_role_markers": tx_text.count("openrefRole"),
        "tx_autotx_markers": tx_text.count("openrefAutoTx"),
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
        description="Run OpenRef AutoRole using one image and RAILtest setmemw role selection."
    )
    parser.add_argument("--rx-port", required=True)
    parser.add_argument("--tx-port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration-seconds", type=float, default=30.0)
    parser.add_argument("--expected-rx", type=int, default=50)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument("--role-address", type=lambda value: int(value, 0))
    parser.add_argument("--payload-address", type=lambda value: int(value, 0))
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    role_address = args.role_address
    if role_address is None:
        role_address = resolve_symbol_address(nm_path=args.nm, elf_path=args.elf)
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

    if args.payload_bytes < 0 or args.payload_bytes > 255:
        parser.error("--payload-bytes must be between 0 and 255")

    raise SystemExit(
        run_autorole(
            rx_port=args.rx_port,
            tx_port=args.tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            duration_seconds=args.duration_seconds,
            expected_rx=args.expected_rx,
            role_address=role_address,
            payload_address=payload_address,
            payload_bytes=args.payload_bytes,
            rf_path=args.rf_path,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
