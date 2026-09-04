#!/usr/bin/env python3
"""Audit whether current evidence supports an OpenRef MVP claim."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from audit_prototype0_gates import audit as audit_prototype0
from validate_audio_benchmark_result import validate_result
from validate_requirement_traceability import validate as validate_traceability


ROOT = Path(__file__).parents[1]
DEFAULT_CHECKLIST = ROOT / "hardware/prototype1-wearable/readiness-checklist.md"
DEFAULT_VERIFICATION_MATRIX = ROOT / "docs/testing/architecture-verification-matrix.md"
DEFAULT_REQUIREMENT_FILES = (
    ROOT / "docs/requirements/requirements-register.md",
    ROOT / "docs/requirements/subsystem-requirements.md",
)
VERIFICATION_SCHEMA = "openref-architecture-verification-evidence-v2"
MINIMUM_PROTOTYPE1_CHECKLIST_ITEMS = 25


def _load_json(path: Path | None) -> tuple[Any | None, list[str]]:
    if path is None:
        return None, ["no paced-target audio benchmark result supplied"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"cannot load audio benchmark result: {error}"]


def _checklist(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return {"path": str(path), "complete": False, "checked": 0, "total": 0,
                "open": [], "failures": [str(error)]}
    checkbox_lines = re.findall(r"^- \[[^\r\n]*$", text, flags=re.MULTILINE)
    candidate_lines = re.findall(r"^- \[([^\]]*)\] (.+)$", text, flags=re.MULTILINE)
    malformed_syntax = len(checkbox_lines) - len(candidate_lines)
    malformed = ([f"{malformed_syntax} malformed checklist item(s)"]
                 if malformed_syntax else []) + [
        f"unsupported checklist mark [{mark}] for {label}"
        for mark, label in candidate_lines if mark not in {" ", "x", "X"}
    ]
    items = [(mark, label) for mark, label in candidate_lines
             if mark in {" ", "x", "X"}]
    checked = [label for mark, label in items if mark.lower() == "x"]
    open_items = [label for mark, label in items if mark == " "]
    if len(items) < MINIMUM_PROTOTYPE1_CHECKLIST_ITEMS:
        malformed.append(
            f"checklist has {len(items)} recognized items; expected at least "
            f"{MINIMUM_PROTOTYPE1_CHECKLIST_ITEMS}"
        )
    return {
        "path": str(path),
        "complete": bool(items) and not open_items and not malformed,
        "checked": len(checked),
        "total": len(items),
        "open": open_items,
        "failures": malformed + ([] if items else ["no checklist items found"]),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verification_ids(matrix: Path = DEFAULT_VERIFICATION_MATRIX) -> tuple[list[str], list[str]]:
    try:
        text = matrix.read_text(encoding="utf-8")
    except OSError as error:
        return [], [f"cannot read verification matrix: {error}"]
    identifiers = re.findall(r"^\| (AV-\d{3}) \|", text, flags=re.MULTILINE)
    failures = []
    duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if not identifiers:
        failures.append("verification matrix contains no AV test identifiers")
    if duplicates:
        failures.append(f"verification matrix has duplicate test identifiers: {', '.join(duplicates)}")
    return identifiers, failures


def _verification_evidence(
    manifest: Path | None,
    matrix: Path = DEFAULT_VERIFICATION_MATRIX,
    requirement_files: tuple[Path, ...] = DEFAULT_REQUIREMENT_FILES,
) -> dict[str, Any]:
    expected, failures = _verification_ids(matrix)
    try:
        failures.extend(validate_traceability(list(requirement_files), matrix))
    except OSError as error:
        failures.append(f"cannot validate requirement traceability: {error}")
    report: dict[str, Any] = {
        "path": str(manifest) if manifest else None,
        "matrix": str(matrix),
        "expected": len(expected),
        "passed": 0,
        "failures": list(failures),
    }
    if manifest is None:
        report["failures"].append("no architecture-verification evidence manifest supplied")
        return report
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        report["failures"].append(f"cannot load verification evidence manifest: {error}")
        return report
    if not isinstance(data, dict):
        report["failures"].append("verification evidence manifest root must be a JSON object")
        return report
    if data.get("schema") != VERIFICATION_SCHEMA:
        report["failures"].append(f"schema must equal {VERIFICATION_SCHEMA!r}")
    matrix_hash = data.get("matrix_sha256")
    if not isinstance(matrix_hash, str) or re.fullmatch(r"[0-9a-f]{64}", matrix_hash) is None:
        report["failures"].append("matrix_sha256 must be 64 lowercase hex digits")
    else:
        try:
            current_matrix_hash = _sha256(matrix)
        except OSError as error:
            report["failures"].append(f"cannot hash verification matrix: {error}")
        else:
            if matrix_hash != current_matrix_hash:
                report["failures"].append(
                    f"matrix_sha256 mismatch: {matrix_hash} != {current_matrix_hash}"
                )
    results = data.get("results")
    if not isinstance(results, list):
        report["failures"].append("results must be a list")
        return report

    seen: set[str] = set()
    passed = 0
    expected_set = set(expected)
    for index, item in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(item, dict):
            report["failures"].append(f"{prefix} must be a JSON object")
            continue
        test_id = item.get("id")
        if not isinstance(test_id, str) or test_id not in expected_set:
            report["failures"].append(f"{prefix}.id is not a matrix test identifier")
            continue
        if test_id in seen:
            report["failures"].append(f"duplicate result for {test_id}")
            continue
        seen.add(test_id)
        if item.get("status") != "passed":
            report["failures"].append(f"{test_id}.status must equal 'passed'")
            continue
        for field in ("procedure", "conclusion", "executor", "executed_at"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                report["failures"].append(f"{test_id}.{field} must be non-empty")
        executed_at = item.get("executed_at")
        if (isinstance(executed_at, str) and
                re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", executed_at) is None):
            report["failures"].append(f"{test_id}.executed_at must be UTC RFC3339 seconds")
        configuration = item.get("configuration")
        if not isinstance(configuration, dict):
            report["failures"].append(f"{test_id}.configuration must be a JSON object")
        else:
            for field in ("hardware_revision", "firmware_revision"):
                value = configuration.get(field)
                if not isinstance(value, str) or not value.strip():
                    report["failures"].append(
                        f"{test_id}.configuration.{field} must be non-empty"
                    )
        reviewer = item.get("reviewer")
        if not isinstance(reviewer, dict):
            report["failures"].append(f"{test_id}.reviewer must be a JSON object")
        else:
            for field in ("name", "reviewed_at"):
                value = reviewer.get(field)
                if not isinstance(value, str) or not value.strip():
                    report["failures"].append(f"{test_id}.reviewer.{field} must be non-empty")
            reviewed_at = reviewer.get("reviewed_at")
            if (isinstance(reviewed_at, str) and
                    re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", reviewed_at) is None):
                report["failures"].append(
                    f"{test_id}.reviewer.reviewed_at must be UTC RFC3339 seconds"
                )
            if (isinstance(reviewer.get("name"), str) and
                    isinstance(item.get("executor"), str) and
                    reviewer["name"].strip().casefold() == item["executor"].strip().casefold()):
                report["failures"].append(f"{test_id}.reviewer must be independent of executor")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            report["failures"].append(f"{test_id}.evidence must be a non-empty list")
            continue
        evidence_valid = True
        for evidence_index, artifact in enumerate(evidence):
            artifact_prefix = f"{test_id}.evidence[{evidence_index}]"
            if not isinstance(artifact, dict):
                report["failures"].append(f"{artifact_prefix} must be a JSON object")
                evidence_valid = False
                continue
            path_text = artifact.get("path")
            expected_hash = artifact.get("sha256")
            expected_bytes = artifact.get("bytes")
            for field in ("role", "media_type"):
                if not isinstance(artifact.get(field), str) or not artifact[field].strip():
                    report["failures"].append(f"{artifact_prefix}.{field} must be non-empty")
                    evidence_valid = False
            if not isinstance(path_text, str) or not path_text:
                report["failures"].append(f"{artifact_prefix}.path must be non-empty")
                evidence_valid = False
                continue
            artifact_path = Path(path_text)
            if not artifact_path.is_absolute():
                artifact_path = manifest.parent / artifact_path
            if (not isinstance(expected_hash, str) or
                    re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None):
                report["failures"].append(f"{artifact_prefix}.sha256 must be 64 lowercase hex digits")
                evidence_valid = False
                continue
            try:
                actual_hash = _sha256(artifact_path)
                actual_bytes = artifact_path.stat().st_size
            except OSError as error:
                report["failures"].append(f"{artifact_prefix} cannot be read: {error}")
                evidence_valid = False
                continue
            if actual_hash != expected_hash:
                report["failures"].append(
                    f"{artifact_prefix}.sha256 mismatch: {expected_hash} != {actual_hash}"
                )
                evidence_valid = False
            if not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes < 0:
                report["failures"].append(f"{artifact_prefix}.bytes must be a non-negative integer")
                evidence_valid = False
            elif actual_bytes != expected_bytes:
                report["failures"].append(
                    f"{artifact_prefix}.bytes mismatch: {expected_bytes} != {actual_bytes}"
                )
                evidence_valid = False
        item_failures = [failure for failure in report["failures"]
                         if failure.startswith(f"{test_id}.")]
        if evidence_valid and not item_failures:
            passed += 1
    missing = sorted(expected_set - seen)
    if missing:
        report["failures"].append(f"missing verification results: {', '.join(missing)}")
    report["passed"] = passed
    return report


def audit_mvp(
    prototype0_root: Path,
    audio_result: Path | None,
    checklist: Path = DEFAULT_CHECKLIST,
    verification_result: Path | None = None,
    verification_matrix: Path = DEFAULT_VERIFICATION_MATRIX,
) -> dict[str, Any]:
    radio = audit_prototype0(prototype0_root)
    radio_failures = [
        f"{gate['gate']}: {gate['status']}"
        for gate in radio["gates"] if gate["status"] != "passed"
    ]
    audio_data, audio_load_failures = _load_json(audio_result)
    audio_failures = audio_load_failures
    if audio_data is not None:
        audio_failures = validate_result(audio_data)
    hardware = _checklist(checklist)
    verification = _verification_evidence(verification_result, verification_matrix)
    gates = [
        {
            "id": "MVP-RADIO",
            "name": "Prototype 0 radio evidence",
            "passed": not radio_failures,
            "failures": radio_failures,
        },
        {
            "id": "MVP-AUDIO",
            "name": "Paced target audio processor promotion",
            "passed": not audio_failures,
            "failures": audio_failures,
        },
        {
            "id": "MVP-HARDWARE",
            "name": "Prototype 1 custom-PCB readiness",
            "passed": hardware["complete"],
            "failures": hardware["failures"] + hardware["open"],
        },
        {
            "id": "MVP-VERIFICATION",
            "name": "Architecture verification evidence",
            "passed": not verification["failures"],
            "failures": verification["failures"],
        },
    ]
    return {
        "schema": "openref-mvp-readiness-v1",
        "passed": all(gate["passed"] for gate in gates),
        "gates": gates,
        "prototype0": radio,
        "audio_result": str(audio_result) if audio_result else None,
        "hardware_checklist": hardware,
        "verification_evidence": verification,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# OpenRef MVP Readiness Audit", "", "| Gate | Status | Blocking evidence |",
             "|---|---|---|"]
    for gate in report["gates"]:
        failures = "<br>".join(
            html.escape(str(failure), quote=False).replace("|", "&#124;")
            for failure in gate["failures"]
        ) or "none"
        name = html.escape(f"{gate['id']} {gate['name']}", quote=False).replace("|", "&#124;")
        lines.append(f"| {name} | {'PASS' if gate['passed'] else 'OPEN'} | {failures} |")
    lines.extend(["", f"Overall: **{'PASS' if report['passed'] else 'NOT READY'}**", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype0-root", type=Path,
                        default=ROOT / "firmware/prototype0/fg23")
    parser.add_argument("--audio-result", type=Path)
    parser.add_argument("--checklist", type=Path, default=DEFAULT_CHECKLIST)
    parser.add_argument("--verification-result", type=Path)
    parser.add_argument("--verification-matrix", type=Path,
                        default=DEFAULT_VERIFICATION_MATRIX)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()
    report = audit_mvp(
        args.prototype0_root, args.audio_result, args.checklist,
        args.verification_result, args.verification_matrix,
    )
    rendered = render_markdown(report)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(rendered, encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
