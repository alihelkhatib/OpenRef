from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from openref_autorole_run import (
    DEFAULT_ELF,
    DEFAULT_NM,
    PAYLOAD_SYMBOL,
    resolve_named_symbol_address,
    resolve_symbol_address,
    run_autorole,
)
from railtest_smoke import discover_segger_serial_ports


def run_sweep(
    *,
    rx_port: str,
    tx_port: str,
    payloads: list[int],
    duration_seconds: float,
    expected_rx: int,
    rf_path: int,
    output_dir: Path,
    nm_path: Path,
    elf_path: Path,
) -> int:
    date = datetime.now().strftime("%Y%m%d")
    role_address = resolve_symbol_address(nm_path=nm_path, elf_path=elf_path)
    payload_address = resolve_named_symbol_address(
        nm_path=nm_path,
        elf_path=elf_path,
        symbol=PAYLOAD_SYMBOL,
    )

    results = []
    failures = 0
    for payload in payloads:
        summary_json = output_dir / (
            f"{date}-openref-autorole-capacity-payload-{payload}-summary.json"
        )
        print(
            f"payload_bytes={payload} duration_seconds={duration_seconds} "
            f"expected_rx={expected_rx}"
        )
        result = run_autorole(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=output_dir,
            baud=115200,
            duration_seconds=duration_seconds,
            expected_rx=expected_rx,
            role_address=role_address,
            payload_address=payload_address,
            payload_bytes=payload,
            rf_path=rf_path,
            summary_json=summary_json,
        )
        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        results.append(summary)
        if result != 0:
            failures += 1

    aggregate = output_dir / f"{date}-openref-autorole-capacity-sweep-summary.json"
    aggregate.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(f"wrote {aggregate}")
    return 0 if failures == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an OpenRef AutoRole runtime payload capacity sweep."
    )
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--payloads", nargs="+", type=int, default=[16, 60, 120, 200])
    parser.add_argument("--duration-seconds", type=float, default=60.0)
    parser.add_argument("--expected-rx", type=int, default=120)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
    parser.add_argument("--elf", type=Path, default=DEFAULT_ELF)
    parser.add_argument("--nm", type=Path, default=DEFAULT_NM)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    args = parser.parse_args()

    invalid_payloads = [payload for payload in args.payloads if payload < 0 or payload > 255]
    if invalid_payloads:
        parser.error(f"payloads must be between 0 and 255: {invalid_payloads}")

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
        run_sweep(
            rx_port=rx_port,
            tx_port=tx_port,
            payloads=args.payloads,
            duration_seconds=args.duration_seconds,
            expected_rx=args.expected_rx,
            rf_path=args.rf_path,
            output_dir=args.output_dir,
            nm_path=args.nm,
            elf_path=args.elf,
        )
    )


if __name__ == "__main__":
    main()
