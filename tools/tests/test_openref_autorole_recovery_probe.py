import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "openref_autorole_recovery_probe.py"


def test_autorole_recovery_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "OpenRef AutoRole role-cycle recovery checks" in result.stdout
