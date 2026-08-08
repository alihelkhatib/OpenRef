import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "capture_serial.py"


def test_capture_serial_requires_port_and_output() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--port and --output are required" in result.stderr


def test_capture_serial_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Capture OpenRef serial logs" in result.stdout
    assert "--send-line" in result.stdout
