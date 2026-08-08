from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re

from railtest_pair_smoke import run_pair_smoke
from railtest_smoke import discover_segger_serial_ports


FIELD_RE = re.compile(r"\{([A-Za-z0-9_]+):([^{}]+)\}")


def parse_last_event_fields(text: str, event: str) -> dict[str, str]:
    marker = "{{(" + event + ")}"
    index = text.rfind(marker)
    if index == -1:
        return {}
    line_end = text.find("\n", index)
    line = text[index:] if line_end == -1 else text[index:line_end]
    return {key: value for key, value in FIELD_RE.findall(line)}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def to_int(fields: dict[str, str], key: str) -> int | None:
    value = fields.get(key)
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def summarize_run(
    *,
    rx_log: Path,
    tx_log: Path,
    requested_packets: int,
    payload_bytes: int,
    tx_delay_ms: int | None,
    rx_port: str,
    tx_port: str,
    rf_path: int | None,
) -> dict[str, object]:
    rx_text = read_text(rx_log)
    tx_text = read_text(tx_log)
    rx_status = parse_last_event_fields(rx_text, "status")
    tx_status = parse_last_event_fields(tx_text, "status")
    tx_end = parse_last_event_fields(tx_text, "txEnd")

    rx_count = to_int(rx_status, "RxCount")
    sync_detect = to_int(rx_status, "SyncDetect")
    crc_drop = to_int(rx_status, "RxCrcErrDrop")
    transmitted = to_int(tx_end, "transmitted")
    failed = to_int(tx_end, "failed")

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rx_port": rx_port,
        "tx_port": tx_port,
        "rf_path": rf_path,
        "requested_packets": requested_packets,
        "payload_bytes": payload_bytes,
        "tx_delay_ms": tx_delay_ms,
        "transmitted_packets": transmitted,
        "tx_failed_packets": failed,
        "rx_count": rx_count,
        "sync_detect": sync_detect,
        "rx_crc_drop": crc_drop,
        "delivery_ratio": (
            rx_count / transmitted
            if rx_count is not None and transmitted not in (None, 0)
            else None
        ),
        "rx_status": rx_status,
        "tx_status": tx_status,
        "tx_end": tx_end,
        "rx_log": str(rx_log),
        "tx_log": str(tx_log),
    }


def run_packet_check(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    packets: int,
    payload_bytes: int,
    tx_delay_ms: int | None,
    settle_seconds: float,
    rf_path: int | None,
    summary_json: Path | None,
) -> int:
    result = run_pair_smoke(
        rx_port=rx_port,
        tx_port=tx_port,
        output_dir=output_dir,
        baud=baud,
        packets=packets,
        payload_bytes=payload_bytes,
        tx_delay_ms=tx_delay_ms,
        settle_seconds=settle_seconds,
        rf_path=rf_path,
    )

    date = datetime.now().strftime("%Y%m%d")
    rx_log = output_dir / f"{date}-railtest-pair-rx.log"
    tx_log = output_dir / f"{date}-railtest-pair-tx.log"
    summary = summarize_run(
        rx_log=rx_log,
        tx_log=tx_log,
        requested_packets=packets,
        payload_bytes=payload_bytes,
        tx_delay_ms=tx_delay_ms,
        rx_port=rx_port,
        tx_port=tx_port,
        rf_path=rf_path,
    )
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)

    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(rendered + "\n", encoding="utf-8")

    if result != 0:
        return result
    expected = summary["transmitted_packets"] == packets and summary["rx_count"] == packets
    return 0 if expected else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run and summarize a two-board FG23 RAILtest packet check."
    )
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--packets", type=int, default=20)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--tx-delay-ms", type=int)
    parser.add_argument("--settle-seconds", type=float, default=5)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
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
        run_packet_check(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
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
