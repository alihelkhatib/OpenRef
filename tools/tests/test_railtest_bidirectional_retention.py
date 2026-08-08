import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_bidirectional_retention.py"
sys.path.insert(0, str(SCRIPT.parents[0]))

import railtest_bidirectional_retention
from railtest_bidirectional_retention import run_bidirectional_retention


def test_run_bidirectional_retention_runs_both_directions(tmp_path: Path, monkeypatch) -> None:
    calls = []

    def fake_run_packet_check(**kwargs):
        calls.append(kwargs)
        kwargs["summary_json"].parent.mkdir(parents=True, exist_ok=True)
        kwargs["summary_json"].write_text(
            json.dumps(
                {
                    "transmitted_packets": kwargs["packets"],
                    "tx_failed_packets": 0,
                    "rx_count": kwargs["packets"],
                    "rx_crc_drop": 0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(
        railtest_bidirectional_retention,
        "run_packet_check",
        fake_run_packet_check,
    )

    report = run_bidirectional_retention(
        rx_port="COM8",
        tx_port="COM10",
        output_root=tmp_path,
        packets=200,
    )

    assert report["pass"] is True
    assert [(call["rx_port"], call["tx_port"]) for call in calls] == [
        ("COM8", "COM10"),
        ("COM10", "COM8"),
    ]
    assert [item["pass"] for item in report["directions"]] == [True, True]


def test_run_bidirectional_retention_fails_on_counter_mismatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    count = 0

    def fake_run_packet_check(**kwargs):
        nonlocal count
        count += 1
        rx_count = kwargs["packets"] if count == 1 else kwargs["packets"] - 1
        kwargs["summary_json"].parent.mkdir(parents=True, exist_ok=True)
        kwargs["summary_json"].write_text(
            json.dumps(
                {
                    "transmitted_packets": kwargs["packets"],
                    "tx_failed_packets": 0,
                    "rx_count": rx_count,
                    "rx_crc_drop": 0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(
        railtest_bidirectional_retention,
        "run_packet_check",
        fake_run_packet_check,
    )

    report = run_bidirectional_retention(
        rx_port="COM8",
        tx_port="COM10",
        output_root=tmp_path,
        packets=200,
    )

    assert report["pass"] is False
    assert report["directions"][0]["pass"] is True
    assert report["directions"][1]["pass"] is False
    assert "packet counters did not match" in report["directions"][1]["failures"][0]
