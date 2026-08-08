from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import time

from capture_serial import _load_serial
from railtest_pair_smoke import write_command
from railtest_smoke import discover_segger_serial_ports


RSSI_RE = re.compile(r"\{rssi:([-0-9.]+)\}")


def read_for(handle, seconds: float) -> str:
    deadline = time.monotonic() + seconds
    chunks = []
    while time.monotonic() < deadline:
        raw = handle.readline()
        if raw:
            text = raw.decode("utf-8", errors="replace")
            print(text, end="")
            chunks.append(text)
    return "".join(chunks)


def command(handle, text: str, wait_seconds: float = 0.5) -> str:
    write_command(handle, text)
    return read_for(handle, wait_seconds)


def parse_rssi(text: str) -> float | None:
    matches = RSSI_RE.findall(text)
    if not matches:
        return None
    return float(matches[-1])


def summarize_rssi(
    *,
    rx_port: str,
    tx_port: str,
    rf_path: int | None,
    baseline_rssi_dbm: float | None,
    tone_rssi_dbm: float | None,
    min_delta_db: float,
    expect: str = "tone",
) -> dict[str, object]:
    delta_db = (
        tone_rssi_dbm - baseline_rssi_dbm
        if baseline_rssi_dbm is not None and tone_rssi_dbm is not None
        else None
    )
    tone_detected = delta_db is not None and delta_db >= min_delta_db
    passed = tone_detected if expect == "tone" else not tone_detected
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rx_port": rx_port,
        "tx_port": tx_port,
        "rf_path": rf_path,
        "baseline_rssi_dbm": baseline_rssi_dbm,
        "tone_rssi_dbm": tone_rssi_dbm,
        "delta_db": delta_db,
        "min_delta_db": min_delta_db,
        "expect": expect,
        "tone_detected": tone_detected,
        "pass": passed,
    }


def run_probe(
    *,
    rx_port: str,
    tx_port: str,
    baud: int,
    rf_path: int | None,
    min_delta_db: float,
    expect: str,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        with serial.Serial(tx_port, baudrate=baud, timeout=0.1) as tx_handle:
            command(rx_handle, "rx 0", 0.3)
            command(tx_handle, "rx 0", 0.3)
            if rf_path is not None:
                command(rx_handle, f"setRfPath {rf_path}", 0.3)
                command(tx_handle, f"setRfPath {rf_path}", 0.3)
            command(tx_handle, "setTxTone 0", 0.3)
            command(rx_handle, "rx 1", 0.3)
            baseline = parse_rssi(command(rx_handle, "getRssi 1", 1.0))
            command(tx_handle, "setTxTone 1", 0.5)
            time.sleep(0.5)
            tone = parse_rssi(command(rx_handle, "getRssi 1", 1.0))
            command(tx_handle, "setTxTone 0", 0.5)
            command(rx_handle, "rx 0", 0.3)

    summary = summarize_rssi(
        rx_port=rx_port,
        tx_port=tx_port,
        rf_path=rf_path,
        baseline_rssi_dbm=baseline,
        tone_rssi_dbm=tone,
        min_delta_db=min_delta_db,
        expect=expect,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(rendered + "\n", encoding="utf-8")

    if baseline is None or tone is None:
        print("FAIL: could not parse RSSI")
        return 1
    if summary["pass"] and expect == "tone":
        print("PASS: receiver saw TX tone energy")
        return 0
    if summary["pass"]:
        print("PASS: receiver stayed near noise floor as expected")
        return 0
    if expect == "no-tone":
        print("FAIL: receiver saw TX tone energy unexpectedly")
    else:
        print("FAIL: receiver did not see clear TX tone energy")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe two-board RAILtest RSSI.")
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument("--min-delta-db", type=float, default=10.0)
    parser.add_argument("--expect", choices=("tone", "no-tone"), default="tone")
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
        run_probe(
            rx_port=rx_port,
            tx_port=tx_port,
            baud=args.baud,
            rf_path=args.rf_path,
            min_delta_db=args.min_delta_db,
            expect=args.expect,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
