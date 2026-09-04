import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import create_release_provenance as provenance
import verify_release_provenance as verifier


def run_git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "test@example.invalid")
    run_git(repo, "config", "user.name", "Test")
    (repo / "tracked.c").write_text("one\n")
    run_git(repo, "add", "tracked.c")
    run_git(repo, "commit", "-m", "initial")
    return repo


def test_manifest_binds_dirty_source_artifacts_and_reports(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "tracked.c").write_text("two\n")
    (repo / "new.c").write_text("new\n")
    elf = tmp_path / "firmware.elf"
    report = tmp_path / "native.txt"
    elf.write_bytes(b"ELF")
    report.write_text("48/48 passed\n")
    output = repo / "release.json"
    doc = provenance.build_manifest(
        repo, output, [f"firmware_elf={elf}"],
        [f"native=passed:{report}"], ["arm_gnu=14.3.1"],
    )
    assert doc["source"]["dirty"] is True
    assert any(item["location"] == "new.c" for item in doc["source"]["untracked_files"])
    assert doc["artifacts"][0]["sha256"] == hashlib.sha256(b"ELF").hexdigest()
    assert doc["validations"][0]["declared_status"] == "passed"
    assert doc["claims"]["release_ready"] is False


def test_output_is_excluded_and_manifest_is_deterministic(tmp_path):
    repo = make_repo(tmp_path)
    artifact = repo / "firmware.bin"
    artifact.write_bytes(b"binary")
    output = repo / "release.json"
    first = provenance.build_manifest(repo, output, [f"binary={artifact}"], [], [])
    output.write_text(json.dumps(first))
    second = provenance.build_manifest(repo, output, [f"binary={artifact}"], [], [])
    assert first == second


def test_missing_artifact_and_unbound_pass_are_rejected(tmp_path):
    repo = make_repo(tmp_path)
    output = repo / "release.json"
    try:
        provenance.build_manifest(repo, output, [f"elf={repo / 'missing'}"], [], [])
        assert False
    except FileNotFoundError:
        pass
    try:
        provenance.build_manifest(repo, output, [], ["native=passed"], [])
        assert False
    except ValueError as exc:
        assert "STATUS:REPORT" in str(exc)


def test_verifier_detects_artifact_mutation(tmp_path):
    repo = make_repo(tmp_path)
    artifact = repo / "firmware.bin"
    artifact.write_bytes(b"original")
    output = repo / "release.json"
    doc = provenance.build_manifest(repo, output, [f"binary={artifact}"], [], [])
    output.write_text(json.dumps(doc))
    assert verifier.verify(doc, repo, {}, {}, output) == []
    artifact.write_bytes(b"changed")
    errors = verifier.verify(doc, repo, {}, {}, output)
    assert any("SHA-256 mismatch" in error for error in errors)


def test_duplicate_semantic_names_are_rejected(tmp_path):
    repo = make_repo(tmp_path)
    artifact = repo / "firmware.bin"
    artifact.write_bytes(b"x")
    try:
        provenance.build_manifest(repo, repo / "out.json", [f"elf={artifact}", f"elf={artifact}"], [], [])
        assert False
    except ValueError as exc:
        assert "duplicate artifact role" in str(exc)
