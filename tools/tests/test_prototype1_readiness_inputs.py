import hashlib
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "prototype1_readiness_inputs.py"
SPEC = importlib.util.spec_from_file_location("prototype1_readiness_inputs", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
INPUTS, SCHEMA = MODULE.INPUTS, MODULE.SCHEMA
template, validate = MODULE.template, MODULE.validate


def test_template_contains_exactly_nine_open_inputs(tmp_path: Path) -> None:
    data = template()
    assert data["schema"] == SCHEMA
    assert [item["id"] for item in data["inputs"]] == list(INPUTS)
    assert len(data["inputs"]) == 9
    assert {item["status"] for item in data["inputs"]} == {"open"}
    failures = validate(data, tmp_path / "manifest.json")
    assert len([failure for failure in failures if "remains open" in failure]) == 9


def test_verified_inputs_require_provenance_and_decision_metadata(tmp_path: Path) -> None:
    data = template()
    data["inputs"][0]["status"] = "verified"
    failures = validate(data, tmp_path / "manifest.json")
    assert any("value must be" in failure for failure in failures)
    assert any("approved_by" in failure for failure in failures)
    assert any("recorded_at" in failure for failure in failures)
    assert any("evidence" in failure for failure in failures)


def test_complete_hash_bound_manifest_validates(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("measured or approved evidence\n", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    data = template()
    for item in data["inputs"]:
        item.update({
            "status": "verified",
            "value": {"decision_or_measurement": "specific recorded result"},
            "approved_by": "Prototype 1 review board",
            "recorded_at": "2026-08-20T12:00:00-04:00",
            "evidence": [{"path": "evidence.txt", "sha256": digest}],
        })
    assert validate(data, tmp_path / "manifest.json") == []


def test_rejects_duplicate_unknown_missing_and_stale_hash(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("evidence\n", encoding="utf-8")
    data = template()
    item = data["inputs"][0]
    item.update({
        "status": "verified",
        "value": {"result": "12 us"},
        "approved_by": "reviewer",
        "recorded_at": "2026-08-20T12:00:00Z",
        "evidence": [{"path": "evidence.txt", "sha256": "0" * 64}],
    })
    data["inputs"].append(dict(data["inputs"][1]))
    data["inputs"].append({"id": "invented", "label": "invented", "status": "open"})
    data["inputs"] = [entry for entry in data["inputs"] if entry["id"] != "control_placement"]
    failures = validate(data, tmp_path / "manifest.json")
    assert any("duplicate" in failure for failure in failures)
    assert any("not a recognized" in failure for failure in failures)
    assert any("missing readiness input 'control_placement'" in failure for failure in failures)
    assert any("sha256 does not match" in failure for failure in failures)
