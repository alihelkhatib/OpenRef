from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from railtest_packet_run import run_packet_check
from railtest_smoke import discover_segger_serial_ports


def run_sweep(
    *,
    rx_port: str,
    tx_port: str,
    payloads: list[int],
    packets: int,
    tx_delay_ms: int,
    settle_seconds: float,
    rf_path: int,
    output_dir: Path,
) -> int:
    date = datetime.now().strftime("%Y%m%d")
    results = []
    failures = 0
    for payload in payloads:
        summary_json = output_dir / (
            f"{date}-railtest-capacity-payload-{payload}-summary.json"
        )
        print(f"payload_bytes={payload} packets={packets} tx_delay_ms={tx_delay_ms}")
        result = run_packet_check(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=output_dir,
            baud=115200,
            packets=packets,
            payload_bytes=payload,
            tx_delay_ms=tx_delay_ms,
            settle_seconds=settle_seconds,
            rf_path=rf_path,
            summary_json=summary_json,
        )
        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        results.append(summary)
        if result != 0:
            failures += 1

    aggregate = output_dir / f"{date}-railtest-capacity-sweep-summary.json"
    aggregate.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(f"wrote {aggregate}")
    return 0 if failures == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small RAILtest payload sweep.")
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--payloads", nargs="+", type=int, default=[16, 60, 120, 200])
    parser.add_argument("--packets", type=int, default=200)
    parser.add_argument("--tx-delay-ms", type=int, default=20)
    parser.add_argument("--settle-seconds", type=float, default=8)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
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
        run_sweep(
            rx_port=rx_port,
            tx_port=tx_port,
            payloads=args.payloads,
            packets=args.packets,
            tx_delay_ms=args.tx_delay_ms,
            settle_seconds=args.settle_seconds,
            rf_path=args.rf_path,
            output_dir=args.output_dir,
        )
    )


if __name__ == "__main__":
    main()
