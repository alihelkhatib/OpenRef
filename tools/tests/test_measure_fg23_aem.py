import argparse
import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "measure_fg23_aem.py"
SPEC = importlib.util.spec_from_file_location("measure_fg23_aem", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_parse_board() -> None:
    assert MODULE.parse_board("node1=440320955") == ("node1", "440320955")


@pytest.mark.parametrize("value", ["node1", "=123", "node=x"])
def test_parse_board_rejects_invalid_value(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        MODULE.parse_board(value)


def test_measure_parses_commander_json(monkeypatch, tmp_path: Path) -> None:
    class Result:
        returncode = 0
        stdout = '{"success": true, "current": 0.012}'
        stderr = ""

    monkeypatch.setattr(MODULE.subprocess, "run", lambda *args, **kwargs: Result())
    result = MODULE.measure(tmp_path / "commander", [("node1", "123")], 1000)
    assert result["all_succeeded"] is True
    assert result["boards"][0]["response"]["current"] == 0.012

