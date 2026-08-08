import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "openref_autorole_capacity_sweep.py"


def test_autorole_capacity_sweep_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "OpenRef AutoRole runtime payload capacity sweep" in result.stdout
