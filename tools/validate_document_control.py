#!/usr/bin/env python3
"""Validate uniqueness and syntax of tracked OpenRef document identifiers."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path


DECLARATION = re.compile(r"^\*\*Document ID:\*\*\s+([^\s]+)\s*$", re.MULTILINE)
VALID_ID = re.compile(r"^OR-[A-Z]{2,4}-\d{3}$")


def validate(root: Path) -> list[str]:
    declarations: dict[str, list[Path]] = defaultdict(list)
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        matches = DECLARATION.findall(text)
        if len(matches) > 1:
            errors.append(f"{path}: multiple document ID declarations")
        for document_id in matches:
            if not VALID_ID.fullmatch(document_id):
                errors.append(f"{path}: invalid document ID {document_id}")
            declarations[document_id].append(path)
    for document_id, paths in sorted(declarations.items()):
        if len(paths) > 1:
            joined = ", ".join(str(path) for path in paths)
            errors.append(f"duplicate document ID {document_id}: {joined}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OpenRef document IDs")
    parser.add_argument("root", nargs="?", type=Path, default=Path("docs"))
    args = parser.parse_args()
    errors = validate(args.root)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
