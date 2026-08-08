from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re


FIELD_RE = re.compile(r"\{([A-Za-z0-9_]+):([^{}]+)\}")


def parse_rx_packets(text: str) -> list[dict[str, str]]:
    packets = []
    for line in text.splitlines():
        if "{{(rxPacket)}" not in line:
            continue
        packets.append({key: value for key, value in FIELD_RE.findall(line)})
    return packets


def convert(rx_log: Path, output: Path, *, node_id: int, source_id: int) -> int:
    packets = parse_rx_packets(rx_log.read_text(encoding="utf-8", errors="replace"))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "event",
                "local_time_us",
                "node_id",
                "sequence",
                "result",
                "detail",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "event": "boot",
                "local_time_us": "0",
                "node_id": node_id,
                "sequence": "0",
                "result": "ok",
                "detail": "source=railtest_converter",
            }
        )
        for sequence, packet in enumerate(packets, start=1):
            detail = (
                f"source={source_id} "
                f"length={packet.get('len', '')} "
                f"rssi={packet.get('rssi', '')} "
                f"lqi={packet.get('lqi', '')} "
                f"crc={1 if packet.get('crc') == 'Pass' else 0}"
            )
            writer.writerow(
                {
                    "event": "rx_done",
                    "local_time_us": packet.get("timeUs", ""),
                    "node_id": node_id,
                    "sequence": sequence,
                    "result": "ok" if packet.get("crc") == "Pass" else "crc_error",
                    "detail": detail,
                }
            )
    return len(packets)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert RAILtest rxPacket logs to OpenRef packet-pair CSV."
    )
    parser.add_argument("rx_log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--node-id", type=int, default=2)
    parser.add_argument("--source-id", type=int, default=1)
    args = parser.parse_args()

    count = convert(
        args.rx_log,
        args.output,
        node_id=args.node_id,
        source_id=args.source_id,
    )
    print(f"converted_rx_packets={count} output={args.output}")


if __name__ == "__main__":
    main()
