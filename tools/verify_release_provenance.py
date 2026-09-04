#!/usr/bin/env python3
"""Verify hashes and source state in an OpenRef release provenance manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import create_release_provenance as provenance


def assignments(values: list[str], kind: str) -> dict[str, Path]:
    result = {}
    for value in values:
        name, filename = provenance.parse_assignment(value, kind)
        if name in result:
            raise ValueError(f"duplicate {kind}: {name}")
        result[name] = Path(filename)
    return result


def verify_record(record: dict, path: Path) -> list[str]:
    errors = []
    try:
        actual_size = path.stat().st_size
        actual_hash = provenance.sha256_file(path)
    except OSError as exc:
        return [f"{record.get('role', 'artifact')}: cannot read {path}: {exc}"]
    if actual_size != record.get("bytes"):
        errors.append(f"{record.get('role')}: byte count mismatch")
    if actual_hash != record.get("sha256"):
        errors.append(f"{record.get('role')}: SHA-256 mismatch")
    return errors


def verify(doc: dict, repo: Path, artifact_paths: dict[str, Path], validation_paths: dict[str, Path], manifest_path: Path) -> list[str]:
    errors = []
    if doc.get("schema") != provenance.SCHEMA:
        errors.append("unsupported schema")
    if doc.get("claims", {}).get("release_ready") is not False:
        errors.append("provenance manifest must not assert release readiness")
    current_source = provenance.source_record(repo, {manifest_path.resolve()})
    if current_source != doc.get("source"):
        errors.append("repository source state does not match manifest")
    seen_roles = set()
    for record in doc.get("artifacts", []):
        role = record.get("role")
        if role in seen_roles:
            errors.append(f"duplicate artifact role: {role}")
            continue
        seen_roles.add(role)
        path = artifact_paths.get(role)
        if path is None and record.get("location_scope") == "repository":
            path = repo / record["location"]
        if path is None:
            errors.append(f"external artifact path required for role: {role}")
        else:
            errors.extend(verify_record(record, path))
    if set(artifact_paths) - seen_roles:
        errors.append("artifact path supplied for role absent from manifest")
    seen_checks = set()
    for check in doc.get("validations", []):
        name = check.get("name")
        if name in seen_checks:
            errors.append(f"duplicate validation: {name}")
            continue
        seen_checks.add(name)
        path = validation_paths.get(name)
        report = check.get("report", {})
        if path is None and report.get("location_scope") == "repository":
            path = repo / report["location"]
        if path is None:
            errors.append(f"external validation report path required for: {name}")
        else:
            errors.extend(verify_record(report, path))
    if set(validation_paths) - seen_checks:
        errors.append("validation path supplied for check absent from manifest")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--artifact", action="append", default=[], metavar="ROLE=PATH")
    parser.add_argument("--validation", action="append", default=[], metavar="NAME=PATH")
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
        errors = verify(doc, args.repo.resolve(strict=True), assignments(args.artifact, "artifact"),
                        assignments(args.validation, "validation"), args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Release provenance verified (this does not assert release readiness).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
