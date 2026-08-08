from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time


def _load_serial():
    try:
        import serial
        from serial.tools import list_ports
    except ImportError as exc:
        raise SystemExit(
            "pyserial is required. Install with: python -m pip install pyserial"
        ) from exc
    return serial, list_ports


def list_serial_ports() -> None:
    _, list_ports = _load_serial()
    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return
    for port in ports:
        print(f"{port.device}\t{port.description}\t{port.hwid}")


def capture(
    *,
    port: str,
    baud: int,
    output: Path,
    duration_seconds: float | None,
    send_line: str | None,
    append: bool,
) -> str:
    serial, _ = _load_serial()
    output.parent.mkdir(parents=True, exist_ok=True)
    deadline = None if duration_seconds is None else time.monotonic() + duration_seconds
    captured = []

    with serial.Serial(port=port, baudrate=baud, timeout=0.5) as handle:
        if send_line is not None:
            handle.write(f"{send_line}\r\n".encode("utf-8"))
            handle.flush()

        mode = "a" if append else "w"
        with output.open(mode, encoding="utf-8", newline="") as log:
            log.write(
                f"# capture_start_utc={datetime.now(timezone.utc).isoformat()} "
                f"port={port} baud={baud}\n"
            )
            if send_line is not None:
                log.write(f"# sent_line={send_line!r}\n")
            log.flush()
            while deadline is None or time.monotonic() < deadline:
                raw = handle.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace")
                captured.append(line)
                sys.stdout.write(line)
                log.write(line)
                log.flush()
            log.write(
                f"# capture_end_utc={datetime.now(timezone.utc).isoformat()} "
                f"port={port}\n"
            )
    return "".join(captured)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture OpenRef serial logs")
    parser.add_argument("--list", action="store_true", help="list serial ports")
    parser.add_argument("--port", help="serial port, such as COM7")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--duration-seconds", type=float)
    parser.add_argument(
        "--send-line",
        help="send one line after opening the port, such as help or an empty string",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="append to the output log instead of overwriting it",
    )
    args = parser.parse_args()

    if args.list:
        list_serial_ports()
        return
    if args.port is None or args.output is None:
        parser.error("--port and --output are required unless --list is used")
    capture(
        port=args.port,
        baud=args.baud,
        output=args.output,
        duration_seconds=args.duration_seconds,
        send_line=args.send_line,
        append=args.append,
    )


if __name__ == "__main__":
    main()
