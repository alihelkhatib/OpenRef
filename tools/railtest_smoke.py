from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import sys

from capture_serial import _load_serial, capture


RAILTEST_MARKERS = (
    "____Application_Configuration____",
    "____Receive_and_Transmit____",
    "getVersion",
)


def port_sort_key(port: str) -> tuple[str, int | str]:
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", port)
    if not match:
        return (port, port)
    return (match.group(1).upper(), int(match.group(2)))


def discover_segger_serial_ports() -> list[str]:
    _, list_ports = _load_serial()
    ports = []
    for port in list_ports.comports():
        hwid = getattr(port, "hwid", "")
        description = getattr(port, "description", "")
        if "VID:PID=1366:1024" in hwid or "J-Link" in description:
            ports.append(port.device)
    return sorted(ports, key=port_sort_key)


def railtest_output_ok(text: str) -> bool:
    return all(marker in text for marker in RAILTEST_MARKERS)


def run_smoke(
    *,
    ports: list[str],
    output_dir: Path,
    baud: int,
    duration_seconds: float,
    command: str,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y%m%d")
    failures = []

    for index, port in enumerate(ports, start=1):
        output = output_dir / f"{date}-node-{index}-railtest-smoke.log"
        print(f"[node-{index}] {port}: sending {command!r}")
        text = capture(
            port=port,
            baud=baud,
            output=output,
            duration_seconds=duration_seconds,
            send_line=command,
            append=False,
        )
        if railtest_output_ok(text):
            print(f"[node-{index}] PASS: RAILtest CLI responded ({output})")
        else:
            print(f"[node-{index}] FAIL: RAILtest markers missing ({output})")
            failures.append(port)

    if failures:
        print(f"FAIL: no valid RAILtest response from: {', '.join(failures)}")
        return 1
    print(f"PASS: {len(ports)} RAILtest board(s) responded")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an FG23 RAILtest serial smoke test."
    )
    parser.add_argument(
        "--ports",
        nargs="+",
        help="serial ports to test, such as COM8 COM10; auto-detects SEGGER ports if omitted",
    )
    parser.add_argument("--expected-count", type=int, default=2)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration-seconds", type=float, default=8)
    parser.add_argument("--command", default="help")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    args = parser.parse_args()

    ports = args.ports if args.ports else discover_segger_serial_ports()
    if len(ports) != args.expected_count:
        print(
            f"FAIL: expected {args.expected_count} SEGGER serial port(s), "
            f"found {len(ports)}: {', '.join(ports) if ports else 'none'}"
        )
        raise SystemExit(1)

    raise SystemExit(
        run_smoke(
            ports=ports,
            output_dir=args.output_dir,
            baud=args.baud,
            duration_seconds=args.duration_seconds,
            command=args.command,
        )
    )


if __name__ == "__main__":
    main()
