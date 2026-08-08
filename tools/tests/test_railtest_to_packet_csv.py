import csv
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_to_packet_csv.py"
sys.path.insert(0, str(SCRIPT.parents[0]))

from railtest_to_packet_csv import convert, parse_rx_packets


def test_parse_rx_packets() -> None:
    text = "{{(rxPacket)}{len:16}{timeUs:123}{crc:Pass}{rssi:-28}{lqi:255}}\n"
    assert parse_rx_packets(text) == [
        {
            "len": "16",
            "timeUs": "123",
            "crc": "Pass",
            "rssi": "-28",
            "lqi": "255",
        }
    ]


def test_convert_railtest_rx_log(tmp_path: Path) -> None:
    rx_log = tmp_path / "rx.log"
    output = tmp_path / "packet.csv"
    rx_log.write_text(
        "{{(rxPacket)}{len:16}{timeUs:123}{crc:Pass}{rssi:-28}{lqi:255}}\n",
        encoding="utf-8",
    )

    count = convert(rx_log, output, node_id=2, source_id=1)

    assert count == 1
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert rows[0]["event"] == "boot"
    assert rows[1]["event"] == "rx_done"
    assert rows[1]["sequence"] == "1"
    assert "rssi=-28" in rows[1]["detail"]
