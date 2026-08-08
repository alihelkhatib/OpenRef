from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import time

from capture_serial import _load_serial
from railtest_packet_run import run_packet_check
from railtest_pair_smoke import write_command
from railtest_smoke import discover_segger_serial_ports


POWER_RE = re.compile(r"\{power:(?P<deci_dbm>-?\d+)\}")


def parse_get_power_deci_dbm(output: str) -> int | None:
    match = POWER_RE.search(output)
    if match is None:
        return None
    return int(match.group("deci_dbm"))


def set_tx_power(*, port: str, baud: int, power_dbm: float) -> float | None:
    serial, _ = _load_serial()
    deci_dbm = round(power_dbm * 10)
    with serial.Serial(port, baudrate=baud, timeout=0.2) as handle:
        handle.reset_input_buffer()
        write_command(handle, "rx 0")
        time.sleep(0.2)
        write_command(handle, f"setPower {deci_dbm}")
        time.sleep(0.4)
        handle.reset_input_buffer()
        write_command(handle, "getPower")
        time.sleep(0.3)
        output = handle.read(4096).decode("utf-8", errors="replace")
    actual_deci_dbm = parse_get_power_deci_dbm(output)
    return None if actual_deci_dbm is None else actual_deci_dbm / 10


def run_tx_power_sweep(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    powers_dbm: list[float],
    restore_power_dbm: float,
    packets: int,
    payload_bytes: int,
    tx_delay_ms: int,
    settle_seconds: float,
    rf_path: int,
    summary_json: Path | None,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []
    failures = 0
    try:
        for power_dbm in powers_dbm:
            label = f"{power_dbm:g}dBm".replace("-", "neg")
            step_summary_json = output_dir / (
                f"{run_id}-railtest-tx-power-{label}-summary.json"
            )
            print(f"tx_power_dbm={power_dbm:g} packets={packets}")
            actual_power_dbm = set_tx_power(port=tx_port, baud=baud, power_dbm=power_dbm)
            result = run_packet_check(
                rx_port=rx_port,
                tx_port=tx_port,
                output_dir=output_dir,
                baud=baud,
                packets=packets,
                payload_bytes=payload_bytes,
                tx_delay_ms=tx_delay_ms,
                settle_seconds=settle_seconds,
                rf_path=rf_path,
                summary_json=step_summary_json,
            )
            summary = json.loads(step_summary_json.read_text(encoding="utf-8"))
            summary["tx_power_dbm"] = power_dbm
            summary["actual_tx_power_dbm"] = actual_power_dbm
            summary["label"] = f"{power_dbm:g} dBm"
            step_summary_json.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            results.append(summary)
            if result != 0:
                failures += 1
    finally:
        restored_power_dbm = set_tx_power(
            port=tx_port, baud=baud, power_dbm=restore_power_dbm
        )

    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        for summary in results:
            summary["restored_tx_power_dbm"] = restored_power_dbm
        summary_json.write_text(
            json.dumps(results, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if failures == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a RAILtest packet sweep across TX power settings."
    )
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--powers-dbm", nargs="+", type=float, default=[14, 0, -10])
    parser.add_argument("--restore-power-dbm", type=float, default=14)
    parser.add_argument("--packets", type=int, default=100)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--tx-delay-ms", type=int, default=20)
    parser.add_argument("--settle-seconds", type=float, default=10)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    if not args.powers_dbm:
        parser.error("--powers-dbm must include at least one power")
    if args.packets < 1:
        parser.error("--packets must be at least 1")
    if args.payload_bytes < 1 or args.payload_bytes > 255:
        parser.error("--payload-bytes must be between 1 and 255")

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
        run_tx_power_sweep(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            powers_dbm=args.powers_dbm,
            restore_power_dbm=args.restore_power_dbm,
            packets=args.packets,
            payload_bytes=args.payload_bytes,
            tx_delay_ms=args.tx_delay_ms,
            settle_seconds=args.settle_seconds,
            rf_path=args.rf_path,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
