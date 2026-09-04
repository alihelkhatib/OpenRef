#!/usr/bin/env python3
"""Create a deterministic, hash-bound OpenRef release provenance manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


SCHEMA = "openref.release-provenance.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(path: Path, repo: Path, role: str) -> dict:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"artifact is not a regular file: {path}")
    try:
        location = resolved.relative_to(repo).as_posix()
        scope = "repository"
    except ValueError:
        location = resolved.name
        scope = "external"
    return {
        "role": role,
        "location": location,
        "location_scope": scope,
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def git(repo: Path, *args: str, binary: bool = False):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        text=not binary, check=False,
    )
    if result.returncode:
        error = result.stderr if not binary else result.stderr.decode(errors="replace")
        raise ValueError(f"git {' '.join(args)} failed: {error.strip()}")
    return result.stdout


def source_record(repo: Path, excluded: set[Path]) -> dict:
    head = git(repo, "rev-parse", "--verify", "HEAD").strip()
    tracked = git(repo, "diff", "--binary", "HEAD", binary=True)
    status_raw = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [item for item in status_raw.split("\0") if item]
    disclosed = []
    untracked = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        code, raw_path = entry[:2], entry[3:]
        if code[0] in "RC" or code[1] in "RC":
            if index >= len(entries):
                raise ValueError("malformed Git rename/copy status")
            original_path = entries[index]
            index += 1
            entry = f"{code} {raw_path} <- {original_path}"
        candidate = (repo / raw_path).resolve()
        if candidate in excluded:
            continue
        disclosed.append(entry)
        if code == "??" and candidate.is_file():
            untracked.append(artifact_record(candidate, repo, "untracked_source"))
    disclosed.sort()
    untracked.sort(key=lambda item: item["location"])
    return {
        "git_head": head,
        "dirty": bool(disclosed),
        "tracked_diff_sha256": hashlib.sha256(tracked).hexdigest(),
        "status_porcelain": disclosed,
        "untracked_files": untracked,
    }


def parse_assignment(value: str, kind: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{kind} must use NAME=VALUE")
    name, payload = value.split("=", 1)
    if not name or not payload:
        raise argparse.ArgumentTypeError(f"{kind} name and value must be non-empty")
    return name, payload


def build_manifest(repo: Path, output: Path, artifacts: list[str], validations: list[str], tools: list[str]) -> dict:
    records = []
    artifact_roles = set()
    for value in artifacts:
        role, filename = parse_assignment(value, "artifact")
        if role in artifact_roles:
            raise ValueError(f"duplicate artifact role: {role}")
        artifact_roles.add(role)
        records.append(artifact_record(Path(filename), repo, role))
    records.sort(key=lambda item: (item["role"], item["location"]))
    checks = []
    check_names = set()
    for value in validations:
        name, payload = parse_assignment(value, "validation")
        if name in check_names:
            raise ValueError(f"duplicate validation name: {name}")
        check_names.add(name)
        if ":" not in payload:
            raise ValueError("validation must use NAME=STATUS:REPORT")
        status, filename = payload.split(":", 1)
        if status not in {"passed", "failed", "not_run"}:
            raise ValueError(f"invalid validation status: {status}")
        report = artifact_record(Path(filename), repo, "validation_report")
        checks.append({"name": name, "declared_status": status, "report": report})
    checks.sort(key=lambda item: item["name"])
    tool_records = []
    tool_names = set()
    for value in tools:
        name, version = parse_assignment(value, "tool")
        if name in tool_names:
            raise ValueError(f"duplicate tool name: {name}")
        tool_names.add(name)
        tool_records.append({"name": name, "version": version})
    tool_records.sort(key=lambda item: item["name"])
    return {
        "schema": SCHEMA,
        "source": source_record(repo, {output.resolve()}),
        "tools": tool_records,
        "artifacts": records,
        "validations": checks,
        "claims": {
            "release_ready": False,
            "note": "Artifact inventory only; readiness requires the independent MVP audit and physical evidence gates.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact", action="append", default=[], metavar="ROLE=PATH")
    parser.add_argument("--validation", action="append", default=[], metavar="NAME=STATUS:REPORT")
    parser.add_argument("--tool", action="append", default=[], metavar="NAME=VERSION")
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        manifest = build_manifest(repo, args.output, args.artifact, args.validation, args.tool)
        encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
        print(f"Release provenance: {args.output}")
        print(f"Manifest SHA-256: {hashlib.sha256(encoded).hexdigest()}")
        print("Release-ready claim: false")
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
