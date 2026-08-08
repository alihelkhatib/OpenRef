import subprocess
import sys
from pathlib import Path

import importlib.util


SCRIPT = Path(__file__).parents[1] / "railtest_tx_power_sweep.py"
TOOLS_DIR = SCRIPT.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
SPEC = importlib.util.spec_from_file_location("railtest_tx_power_sweep", SCRIPT)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_tx_power_sweep_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "packet sweep across TX power settings" in result.stdout


def test_parse_get_power_deci_dbm() -> None:
    output = "getPower\r\n{{(getPower)}{powerLevel:185}{power:140}}\r\n>"

    assert MODULE.parse_get_power_deci_dbm(output) == 140


def test_parse_get_power_deci_dbm_missing() -> None:
    assert MODULE.parse_get_power_deci_dbm("{{(status)}}") is None
