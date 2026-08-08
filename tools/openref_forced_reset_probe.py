from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from capture_serial import _load_serial
from openref_autorole_run import (
    DEFAULT_ELF,
    DEFAULT_NM,
    PAYLOAD_SYMBOL,
    ROLE_SYMBOL,
    resolve_named_symbol_address,
)
from openref_queue_pressure_probe import run_queue_pressure_probe
from railtest_pair_smoke import write_command


def reset_board(*, port: str, baud: int, settle_seconds: float) -> None:
    serial, _ = _load_serial()
    with serial.Serial(port, baudrate=baud, timeout=0.1) as handle:
        write_command(handle, "reset")
        time.sleep(settle_seconds)


def run_forced_reset_probe(
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
    reset_settle_seconds: float,
    summary_json: Path | None,
) -> int:
    date = datetime.now().strftime("%Y%m%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    pre_summary = output_dir / f"{date}-openref-forced-reset-pre-summary.json"
    post_summary = output_dir / f"{date}-openref-forced-reset-post-summary.json"

    pre_result = run_queue_pressure_probe(
        rx_port=rx_port,
        tx_port=tx_port,
        output_dir=output_dir,
        baud=baud,
        packets=packets,
        payload_bytes=payload_bytes,
        command_delay_seconds=command_delay_seconds,
        tx_interval_seconds=tx_interval_seconds,
        rf_path=rf_path,
        role_address=role_address,
        payload_address=payload_address,
        summary_json=pre_summary,
    )
    reset_board(port=rx_port, baud=baud, settle_seconds=reset_settle_seconds)
    post_result = run_queue_pressure_probe(
        rx_port=rx_port,
        tx_port=tx_port,
        output_dir=output_dir,
        baud=baud,
        packets=packets,
        payload_bytes=payload_bytes,
        command_delay_seconds=command_delay_seconds,
        tx_interval_seconds=tx_interval_seconds,
        rf_path=rf_path,
        role_address=role_address,
        payload_address=payload_address,
        summary_json=post_summary,
    )

    pre = json.loads(pre_summary.read_text(encoding="utf-8"))
    post = json.loads(post_summary.read_text(encoding="utf-8"))
    passed = pre_result == 0 and post_result == 0
    summary = {
        "rx_port": rx_port,
        "tx_port": tx_port,
        "packets_per_phase": packets,
        "payload_bytes": payload_bytes,
        "reset_settle_seconds": reset_settle_seconds,
        "pre_reset_pass": pre["pass"],
        "post_reset_pass": post["pass"],
        "post_reset_last_rx": post["last_rx"],
        "post_reset_last_sequence": post["last_sequence"],
        "post_reset_last_gaps": post["last_gaps"],
        "post_reset_last_faults": post["last_faults"],
        "post_reset_rx_status_counters": post["rx_status_counters"],
        "pass": passed,
        "pre_summary": str(pre_summary),
        "post_summary": str(post_summary),
    }
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify OpenRef AutoRole RX recovers after an explicit board reset."
    )
    parser.add_argument("--rx-port", required=True)
    parser.add_argument("--tx-port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--packets", type=int, default=25)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--command-delay-seconds", type=float, default=0.12)
    parser.add_argument("--tx-interval-seconds", type=float, default=0.20)
    parser.add_argument("--reset-settle-seconds", type=float, default=3.0)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument("--role-address", type=lambda value: int(value, 0))
    parser.add_argument("--payload-address", type=lambda value: int(value, 0))
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument("--output-dir", type=Path, default=Path("firmware/prototype0/fg23/results"))
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

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
        run_forced_reset_probe(
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
            reset_settle_seconds=args.reset_settle_seconds,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
