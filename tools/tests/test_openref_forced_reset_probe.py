import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "openref_forced_reset_probe.py"


def test_forced_reset_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "recovers after an explicit board reset" in result.stdout
