from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "extract_audio_benchmark_result.py"
SPEC = importlib.util.spec_from_file_location("extract_audio_benchmark_result", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_extracts_schema_object_from_capture_metadata() -> None:
    text = "# capture_start\nboot\n{\"schema\":\"openref-audio-benchmark-v1\",\"passed\":true}\r\n# capture_end\n"
    assert MODULE.extract_result(text)["passed"] is True


def test_rejects_missing_or_duplicate_results() -> None:
    with pytest.raises(ValueError, match="found 0"):
        MODULE.extract_result("boot only\n")
    result = '{"schema":"openref-audio-benchmark-v1"}\n'
    with pytest.raises(ValueError, match="found 2"):
        MODULE.extract_result(result + result)
