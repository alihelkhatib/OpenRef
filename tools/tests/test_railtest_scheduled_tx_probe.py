import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_scheduled_tx_probe.py"


def test_scheduled_tx_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Probe RAILtest scheduled TX" in result.stdout
