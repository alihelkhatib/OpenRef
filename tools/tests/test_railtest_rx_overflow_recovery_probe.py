import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_rx_overflow_recovery_probe.py"


def test_rx_overflow_recovery_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Force RAILtest RX overflow" in result.stdout
