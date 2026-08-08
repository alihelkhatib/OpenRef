import json
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from analyze_attenuation_sweep import analyze, summarize_step


SCRIPT = Path(__file__).parents[1] / "analyze_attenuation_sweep.py"


def test_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "controlled attenuation packet summaries" in result.stdout


def test_summarize_step_computes_per() -> None:
    step = summarize_step(
        {
            "requested_packets": 100,
            "transmitted_packets": 100,
            "rx_count": 92,
            "rx_crc_drop": 3,
            "attenuation_db": 40,
            "tx_power_dbm": -10,
            "actual_tx_power_dbm": -11.1,
        },
        fallback_label="ignored",
    )

    assert step["label"] == "40"
    assert step["tx_power_dbm"] == -10
    assert step["actual_tx_power_dbm"] == -11.1
    assert step["lost_packets"] == 8
    assert step["delivery_ratio"] == 0.92
    assert round(step["packet_error_rate"], 2) == 0.08


def test_analyze_multiple_summary_files(tmp_path: Path) -> None:
    clean = tmp_path / "clean.json"
    degraded = tmp_path / "degraded.json"
    clean.write_text(
        json.dumps(
            {
                "requested_packets": 100,
                "transmitted_packets": 100,
                "rx_count": 100,
                "delivery_ratio": 1.0,
            }
        ),
        encoding="utf-8",
    )
    degraded.write_text(
        json.dumps(
            {
                "requested_packets": 100,
                "transmitted_packets": 100,
                "rx_count": 80,
            }
        ),
        encoding="utf-8",
    )

    summary = analyze([clean, degraded], labels=["0 dB", "shielded"])

    assert summary["valid_steps"] == 2
    assert summary["degraded_steps"] == 1
    assert summary["worst_step"]["label"] == "shielded"
    assert summary["pass"] is True


def test_analyze_aggregate_list(tmp_path: Path) -> None:
    aggregate = tmp_path / "aggregate.json"
    aggregate.write_text(
        json.dumps(
            [
                {"requested_packets": 50, "transmitted_packets": 50, "rx_count": 50},
                {"requested_packets": 50, "transmitted_packets": 50, "rx_count": 49},
            ]
        ),
        encoding="utf-8",
    )

    summary = analyze([aggregate], min_packet_error_rate=0.01)

    assert summary["valid_steps"] == 2
    assert summary["degraded_steps"] == 1
    assert summary["pass"] is True


def test_fails_without_degraded_step_by_default(tmp_path: Path) -> None:
    aggregate = tmp_path / "aggregate.json"
    aggregate.write_text(
        json.dumps(
            [
                {"requested_packets": 10, "transmitted_packets": 10, "rx_count": 10},
                {"requested_packets": 10, "transmitted_packets": 10, "rx_count": 10},
            ]
        ),
        encoding="utf-8",
    )

    summary = analyze([aggregate])

    assert summary["degraded_steps"] == 0
    assert summary["pass"] is False
