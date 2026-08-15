import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "run_firmware_native_tests.py"


def test_help_lists_required_toolchain_and_output() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--zig" in result.stdout
    assert "--output-dir" in result.stdout

