#!/usr/bin/env python3
"""Create a hash-bound, explicitly unverified architecture evidence package.

This collector inventories existing artifacts.  It deliberately cannot issue a
passing verification result: procedure execution and independent review remain
human-controlled steps in the v2 evidence contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parents[1]
DEFAULT_MATRIX = ROOT / "docs/testing/architecture-verification-matrix.md"
SCHEMA = "openref-architecture-verification-evidence-v2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matrix_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    pattern = re.compile(
        r"^\| (AV-\d{3}) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            rows.append({
                "id": match.group(1),
                "subject": match.group(2).strip(),
                "requirements": match.group(3).strip(),
                "stage": match.group(4).strip(),
                "method": match.group(5).strip(),
            })
    if not rows:
        raise ValueError("verification matrix contains no AV rows")
    return rows


def repository_state(root: Path) -> dict[str, object]:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=root, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        return result.stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
    }


def parse_artifacts(values: list[str], output: Path) -> dict[str, list[dict[str, object]]]:
    by_id: dict[str, list[dict[str, object]]] = {}
    for value in values:
        test_id, separator, path_text = value.partition("=")
        if not separator or re.fullmatch(r"AV-\d{3}", test_id) is None:
            raise ValueError(f"artifact must use AV-NNN=PATH syntax: {value!r}")
        path = Path(path_text).resolve()
        if not path.is_file():
            raise ValueError(f"artifact is not a readable regular file: {path}")
        try:
            stored_path = str(path.relative_to(output.parent.resolve()))
        except ValueError:
            stored_path = str(path)
        by_id.setdefault(test_id, []).append({
            "path": stored_path.replace("\\", "/"),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "role": "unreviewed-supporting-output",
            "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        })
    return by_id


def collect(matrix: Path, output: Path, artifact_values: list[str]) -> dict[str, object]:
    rows = matrix_rows(matrix)
    artifacts = parse_artifacts(artifact_values, output)
    known = {row["id"] for row in rows}
    unknown = sorted(set(artifacts) - known)
    if unknown:
        raise ValueError(f"artifact references unknown matrix IDs: {', '.join(unknown)}")
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "generated_at": now,
        "generator": "tools/collect_architecture_verification_evidence.py",
        "matrix_sha256": sha256(matrix),
        "repository": repository_state(ROOT),
        "results": [
            {
                **row,
                "status": "unverified",
                "evidence": artifacts.get(row["id"], []),
                "blocking_reason": (
                    "requires executed procedure, configuration/revisions, conclusion, "
                    "executor, and independent reviewer approval"
                ),
            }
            for row in rows
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--artifact", action="append", default=[], metavar="AV-NNN=PATH",
        help="attach an existing output without claiming that it closes the AV row",
    )
    args = parser.parse_args()
    try:
        package = collect(args.matrix, args.output, args.artifact)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        parser.error(str(error))
    attached = sum(bool(item["evidence"]) for item in package["results"])
    print(f"Wrote {len(package['results'])} unverified results; {attached} have artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
