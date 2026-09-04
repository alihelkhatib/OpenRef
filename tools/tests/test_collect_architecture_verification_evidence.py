import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "collect_architecture_verification_evidence.py"
SPEC = importlib.util.spec_from_file_location("evidence_collector", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_collector_hashes_outputs_but_never_claims_pass(tmp_path: Path, monkeypatch) -> None:
    matrix = tmp_path / "matrix.md"
    matrix.write_text(
        "| AV-001 | Audio stress | AUD-008 | Bench | Stress test |\n"
        "| AV-002 | Physical latency | AUD-003 | Integrated | Instrumented test |\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "native-tests.log"
    artifact.write_text("48/48 passed\n", encoding="utf-8")
    monkeypatch.setattr(MODULE, "repository_state", lambda root: {"commit": "a" * 40, "dirty": True})
    output = tmp_path / "evidence.json"
    package = MODULE.collect(matrix, output, [f"AV-001={artifact}"])
    assert [item["status"] for item in package["results"]] == ["unverified", "unverified"]
    assert package["results"][0]["evidence"][0]["bytes"] == len(artifact.read_bytes())
    assert len(package["results"][0]["evidence"][0]["sha256"]) == 64
    assert package["results"][1]["evidence"] == []


def test_collector_rejects_unknown_id(tmp_path: Path, monkeypatch) -> None:
    matrix = tmp_path / "matrix.md"
    matrix.write_text("| AV-001 | Audio | AUD-008 | Bench | Test |\n", encoding="utf-8")
    artifact = tmp_path / "out.log"
    artifact.write_text("ok\n", encoding="utf-8")
    monkeypatch.setattr(MODULE, "repository_state", lambda root: {})
    try:
        MODULE.collect(matrix, tmp_path / "result.json", [f"AV-999={artifact}"])
    except ValueError as error:
        assert "unknown matrix IDs" in str(error)
    else:
        raise AssertionError("unknown ID was accepted")
