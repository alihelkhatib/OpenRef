import subprocess
import sys
from pathlib import Path

from openref_queue_pressure_probe import parse_status_counters


SCRIPT = Path(__file__).parents[1] / "openref_queue_pressure_probe.py"


def test_queue_pressure_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "valid OpenRef packet burst" in result.stdout


def test_parse_status_counters_uses_latest_values() -> None:
    text = (
        "{{(status)}{NoRxBuffer:3}{FrameErrors:2}{RxFifoFull:1}{RxOverflow:4}}}"
        "{{(status)}{NoRxBuffer:0}{FrameErrors:0}{RxFifoFull:0}{RxOverflow:0}}}"
    )

    assert parse_status_counters(text) == {
        "RxFifoFull": 0,
        "RxOverflow": 0,
        "NoRxBuffer": 0,
        "FrameErrors": 0,
    }
