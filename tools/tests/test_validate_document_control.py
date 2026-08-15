import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_document_control.py"
SPEC = importlib.util.spec_from_file_location("document_control", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_unique_document_ids_pass(tmp_path: Path) -> None:
    (tmp_path / "one.md").write_text("**Document ID:** OR-TST-100\n", encoding="utf-8")
    (tmp_path / "two.md").write_text("No controlled ID\n", encoding="utf-8")
    assert MODULE.validate(tmp_path) == []


def test_duplicate_and_invalid_document_ids_fail(tmp_path: Path) -> None:
    (tmp_path / "one.md").write_text("**Document ID:** OR-HW-100\n", encoding="utf-8")
    (tmp_path / "two.md").write_text("**Document ID:** OR-HW-100\n", encoding="utf-8")
    (tmp_path / "bad.md").write_text("**Document ID:** bad-id\n", encoding="utf-8")
    errors = MODULE.validate(tmp_path)
    assert any("duplicate document ID" in error for error in errors)
    assert any("invalid document ID" in error for error in errors)
