import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_fault_probe.py"


def test_fault_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Probe safe RAILtest fault recovery" in result.stdout
