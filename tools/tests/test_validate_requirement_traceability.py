import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_requirement_traceability.py"
SPEC = importlib.util.spec_from_file_location("traceability", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_complete_valid_traceability_passes(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.md"
    matrix = tmp_path / "matrix.md"
    requirements.write_text(
        "| SYS-001 | first |\n| AUD-002 | second |\n", encoding="utf-8"
    )
    matrix.write_text(
        "| AV-001 | subject | SYS-001, AUD-002 | stage | Test |\n",
        encoding="utf-8",
    )
    assert MODULE.validate([requirements], matrix) == []


def test_unknown_uncovered_and_duplicate_fail(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.md"
    matrix = tmp_path / "matrix.md"
    requirements.write_text(
        "| SYS-001 | first |\n| AUD-002 | second |\n", encoding="utf-8"
    )
    matrix.write_text(
        "| AV-001 | subject | SYS-001, FW-999 | stage | Test |\n"
        "| AV-001 | duplicate | SYS-001 | stage | Test |\n",
        encoding="utf-8",
    )
    errors = MODULE.validate([requirements], matrix)
    assert "duplicate architecture verification test ID" in errors
    assert "uncovered requirement: AUD-002" in errors
    assert "unknown requirement reference: FW-999" in errors
