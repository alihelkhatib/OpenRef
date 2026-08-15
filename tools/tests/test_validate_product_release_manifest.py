import copy
import hashlib
import json
from pathlib import Path

from validate_product_release_manifest import validate_manifest, verify_artifacts


ROOT = Path(__file__).parents[2]
MANIFEST = ROOT / "docs/testing/product-release-manifest.json"


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def passing_manifest() -> dict:
    data = copy.deepcopy(manifest())
    data.update({
        "release_version": "1.0.0",
        "hardware_revision": "P1-A",
        "radio_firmware_sha256": "1" * 64,
        "audio_firmware_sha256": "2" * 64,
        "system_firmware_sha256": "3" * 64,
        "created_utc": "2026-08-14T12:00:00Z",
        "status": "PASS",
    })
    for gate in data["gates"]:
        gate["status"] = "PASS"
        gate["blocker"] = None
        gate["evidence"] = [{
            "artifact_file": f"{gate['id'].lower()}.json",
            "sha256": "a" * 64,
            "executed_utc": "2026-08-14T11:00:00Z",
            "result": "PASS",
            "test_ids": list(gate["required_tests"]),
        }]
    return data


def test_controlled_manifest_is_structurally_valid_and_reports_all_blockers() -> None:
    errors, blockers = validate_manifest(manifest())
    assert errors == []
    assert len(blockers) == 10


def test_complete_evidence_can_satisfy_the_release_model() -> None:
    assert validate_manifest(passing_manifest()) == ([], [])


def test_top_level_pass_and_partial_gate_evidence_are_rejected() -> None:
    data = manifest()
    data["status"] = "PASS"
    errors, _ = validate_manifest(data)
    assert any("top-level PASS" in error for error in errors)
    data = passing_manifest()
    data["gates"][0]["evidence"][0]["test_ids"].pop()
    errors, _ = validate_manifest(data)
    assert any("PASS lacks evidence" in error for error in errors)


def test_removed_verification_id_and_waiver_status_are_rejected() -> None:
    data = manifest()
    for gate in data["gates"]:
        if "AV-001" in gate["required_tests"]:
            gate["required_tests"].remove("AV-001")
    errors, _ = validate_manifest(data)
    assert any("AV-001 through AV-040" in error for error in errors)
    data = manifest()
    data["gates"][0]["status"] = "WAIVED"
    errors, _ = validate_manifest(data)
    assert any("invalid status" in error for error in errors)


def test_artifact_verification_detects_tampering(tmp_path: Path) -> None:
    data = passing_manifest()
    for gate in data["gates"]:
        item = gate["evidence"][0]
        content = gate["id"].encode()
        (tmp_path / item["artifact_file"]).write_bytes(content)
        item["sha256"] = hashlib.sha256(content).hexdigest()
    assert verify_artifacts(data, tmp_path) == []
    first = data["gates"][0]["evidence"][0]
    (tmp_path / first["artifact_file"]).write_bytes(b"tampered")
    assert any("hash mismatch" in error for error in verify_artifacts(data, tmp_path))
