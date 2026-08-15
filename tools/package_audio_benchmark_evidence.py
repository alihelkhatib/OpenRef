#!/usr/bin/env python3
"""Bind an audio benchmark JSON result to its captured log and build artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def package_evidence(data: dict, artifacts: dict[str, Path], output_dir: Path) -> dict:
    root = output_dir.resolve()
    files: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for key in ("serial_log", "elf", "map"):
        path = artifacts[key].resolve()
        if not path.is_file():
            raise ValueError(f"artifact file is missing: {key}")
        if path.stat().st_size == 0:
            raise ValueError(f"artifact file is empty: {key}")
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"artifact is outside the output directory: {key}") from exc
        files[key] = relative.as_posix()
        hashes[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = dict(data)
    result["artifact_files"] = files
    result["artifact_sha256"] = hashes
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--serial-log", type=Path, required=True)
    parser.add_argument("--elf", type=Path, required=True)
    parser.add_argument("--map", dest="map_file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        print("ERROR: output exists; use --force to replace it")
        return 1
    artifacts = {"serial_log": args.serial_log, "elf": args.elf, "map": args.map_file}
    try:
        data = json.loads(args.result.read_text(encoding="utf-8"))
        packaged = package_evidence(data, artifacts, args.output.parent)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1
    args.output.write_text(json.dumps(packaged, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
