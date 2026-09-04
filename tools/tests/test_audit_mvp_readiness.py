import importlib.util
import hashlib
import json
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "audit_mvp_readiness.py"
SPEC = importlib.util.spec_from_file_location("mvp_audit", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_checklist_requires_every_item(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text("- [x] measured radio\n- [ ] enclosure\n", encoding="utf-8")
    result = MODULE._checklist(checklist)
    assert not result["complete"]
    assert result["checked"] == 1
    assert result["open"] == ["enclosure"]
    assert any("expected at least 25" in failure for failure in result["failures"])


def test_checklist_rejects_unsupported_marks(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text("- [x] measured radio\n- [-] enclosure\n", encoding="utf-8")
    result = MODULE._checklist(checklist)
    assert not result["complete"]
    assert "unsupported checklist mark [-] for enclosure" in result["failures"]


def test_checklist_does_not_pass_after_items_are_deleted(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text("- [x] only surviving item\n", encoding="utf-8")
    result = MODULE._checklist(checklist)
    assert not result["complete"]
    assert result["total"] == 1
    assert any("expected at least 25" in failure for failure in result["failures"])


def test_checklist_rejects_malformed_item_syntax(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    valid = "".join(f"- [x] item {index}\n" for index in range(25))
    checklist.write_text(valid + "- [x]\n", encoding="utf-8")
    result = MODULE._checklist(checklist)
    assert not result["complete"]
    assert "1 malformed checklist item(s)" in result["failures"]


def test_missing_audio_result_is_explicit() -> None:
    data, failures = MODULE._load_json(None)
    assert data is None
    assert failures == ["no paced-target audio benchmark result supplied"]


def test_missing_verification_manifest_is_explicit(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.md"
    requirements = tmp_path / "requirements.md"
    requirements.write_text("| SYS-001 | Requirement |\n", encoding="utf-8")
    matrix.write_text("| AV-001 | Thing | SYS-001 | Bench | Test |\n", encoding="utf-8")
    result = MODULE._verification_evidence(None, matrix, (requirements,))
    assert result["expected"] == 1
    assert result["failures"] == [
        "no architecture-verification evidence manifest supplied"
    ]


def test_verification_manifest_requires_complete_hash_bound_evidence(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.md"
    requirements = tmp_path / "requirements.md"
    requirements.write_text(
        "| SYS-001 | First |\n| SYS-002 | Second |\n", encoding="utf-8"
    )
    matrix.write_text(
        "| AV-001 | First | SYS-001 | Bench | Test |\n"
        "| AV-002 | Second | SYS-002 | Bench | Test |\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "evidence.log"
    artifact.write_text("measured evidence\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = tmp_path / "verification.json"
    def passed(test_id: str) -> dict:
        return {
            "id": test_id, "status": "passed", "procedure": "OR-TP-001",
            "conclusion": "Observed result met the stated acceptance criteria.",
            "executor": "Test Operator", "executed_at": "2026-08-20T12:00:00Z",
            "configuration": {"hardware_revision": "EVT1", "firmware_revision": "abc123"},
            "reviewer": {"name": "Independent Reviewer", "reviewed_at": "2026-08-20T13:00:00Z"},
            "evidence": [{"path": artifact.name, "sha256": digest,
                          "bytes": artifact.stat().st_size, "role": "raw-observation",
                          "media_type": "text/plain"}],
        }
    manifest.write_text(json.dumps({
        "schema": MODULE.VERIFICATION_SCHEMA,
        "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
        "results": [passed("AV-001"), passed("AV-002")],
    }), encoding="utf-8")
    result = MODULE._verification_evidence(manifest, matrix, (requirements,))
    assert result["failures"] == []
    assert result["passed"] == 2

    artifact.write_text("changed evidence\n", encoding="utf-8")
    changed = MODULE._verification_evidence(manifest, matrix, (requirements,))
    assert any("sha256 mismatch" in failure for failure in changed["failures"])


def test_verification_manifest_rejects_missing_and_duplicate_results(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.md"
    requirements = tmp_path / "requirements.md"
    requirements.write_text(
        "| SYS-001 | First |\n| SYS-002 | Second |\n", encoding="utf-8"
    )
    matrix.write_text(
        "| AV-001 | First | SYS-001 | Bench | Test |\n"
        "| AV-002 | Second | SYS-002 | Bench | Test |\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "evidence.log"
    artifact.write_text("evidence\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    row = {"id": "AV-001", "status": "passed", "procedure": "OR-TP-001",
           "conclusion": "pass", "executor": "operator",
           "executed_at": "2026-08-20T12:00:00Z",
           "configuration": {"hardware_revision": "EVT1", "firmware_revision": "abc"},
           "reviewer": {"name": "reviewer", "reviewed_at": "2026-08-20T13:00:00Z"},
           "evidence": [{"path": artifact.name, "sha256": digest,
                         "bytes": artifact.stat().st_size, "role": "raw",
                         "media_type": "text/plain"}]}
    manifest = tmp_path / "verification.json"
    manifest.write_text(json.dumps({
        "schema": MODULE.VERIFICATION_SCHEMA,
        "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
        "results": [row, row],
    }), encoding="utf-8")
    failures = MODULE._verification_evidence(
        manifest, matrix, (requirements,)
    )["failures"]
    assert "duplicate result for AV-001" in failures
    assert "missing verification results: AV-002" in failures


def test_verification_manifest_rejects_self_asserted_hash_only_pass(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.md"
    requirements = tmp_path / "requirements.md"
    requirements.write_text("| SYS-001 | First |\n", encoding="utf-8")
    matrix.write_text("| AV-001 | First | SYS-001 | Bench | Test |\n", encoding="utf-8")
    artifact = tmp_path / "claim.txt"
    artifact.write_text("passed\n", encoding="utf-8")
    manifest = tmp_path / "verification.json"
    manifest.write_text(json.dumps({
        "schema": MODULE.VERIFICATION_SCHEMA,
        "matrix_sha256": hashlib.sha256(matrix.read_bytes()).hexdigest(),
        "results": [{"id": "AV-001", "status": "passed", "evidence": [{
            "path": artifact.name,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }]}],
    }), encoding="utf-8")
    result = MODULE._verification_evidence(manifest, matrix, (requirements,))
    assert result["passed"] == 0
    assert "AV-001.reviewer must be a JSON object" in result["failures"]
    assert any(".bytes must be" in failure for failure in result["failures"])


def test_verification_manifest_is_bound_to_matrix_and_independent_review(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.md"
    requirements = tmp_path / "requirements.md"
    requirements.write_text("| SYS-001 | First |\n", encoding="utf-8")
    matrix.write_text("| AV-001 | First | SYS-001 | Bench | Test |\n", encoding="utf-8")
    artifact = tmp_path / "raw.log"
    artifact.write_text("observation\n", encoding="utf-8")
    manifest = tmp_path / "verification.json"
    manifest.write_text(json.dumps({
        "schema": MODULE.VERIFICATION_SCHEMA,
        "matrix_sha256": "0" * 64,
        "results": [{
            "id": "AV-001", "status": "passed", "procedure": "OR-TP-001",
            "conclusion": "pass", "executor": "Same Person",
            "executed_at": "2026-08-20T12:00:00Z",
            "configuration": {"hardware_revision": "EVT1", "firmware_revision": "abc"},
            "reviewer": {"name": "same person", "reviewed_at": "2026-08-20T13:00:00Z"},
            "evidence": [{
                "path": artifact.name, "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "bytes": artifact.stat().st_size, "role": "raw", "media_type": "text/plain",
            }],
        }],
    }), encoding="utf-8")
    failures = MODULE._verification_evidence(manifest, matrix, (requirements,))["failures"]
    assert any("matrix_sha256 mismatch" in failure for failure in failures)
    assert "AV-001.reviewer must be independent of executor" in failures


def test_verification_gate_rejects_uncovered_requirement(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.md"
    matrix.write_text("| AV-001 | First | SYS-001 | Bench | Test |\n", encoding="utf-8")
    requirements = tmp_path / "requirements.md"
    requirements.write_text(
        "| SYS-001 | First |\n| SYS-002 | Uncovered |\n", encoding="utf-8"
    )
    result = MODULE._verification_evidence(None, matrix, (requirements,))
    assert "uncovered requirement: SYS-002" in result["failures"]


def test_render_does_not_claim_ready() -> None:
    report = {
        "passed": False,
        "gates": [{"id": "MVP-AUDIO", "name": "Audio", "passed": False,
                   "failures": ["measurement missing"]}],
    }
    rendered = MODULE.render_markdown(report)
    assert "Overall: **NOT READY**" in rendered
    assert "measurement missing" in rendered


def test_render_escapes_untrusted_table_content() -> None:
    report = {
        "passed": False,
        "gates": [{"id": "MVP-X", "name": "A|B", "passed": False,
                   "failures": ["bad | <value>"]}],
    }
    rendered = MODULE.render_markdown(report)
    assert "A&#124;B" in rendered
    assert "bad &#124; &lt;value&gt;" in rendered
