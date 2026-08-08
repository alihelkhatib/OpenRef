import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "railtest_capacity_sweep.py"


def test_capacity_sweep_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Run a small RAILtest payload sweep" in result.stdout
