#!/usr/bin/env python3
"""Check that controlled requirements map to valid architecture tests."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIREMENT = re.compile(r"\|\s*((?:SYS|NET|AUD|PWR|FW|MEC)-\d{3})\s*\|")
TEST_ROW = re.compile(r"^\|\s*(AV-\d{3})\s*\|.*$", re.MULTILINE)
REFERENCE = re.compile(r"(?:SYS|NET|AUD|PWR|FW|MEC)-\d{3}")


def validate(requirement_files: list[Path], matrix: Path) -> list[str]:
    requirements: set[str] = set()
    errors: list[str] = []
    for path in requirement_files:
        requirements.update(REQUIREMENT.findall(path.read_text(encoding="utf-8")))
    matrix_text = matrix.read_text(encoding="utf-8")
    rows = TEST_ROW.findall(matrix_text)
    if len(rows) != len(set(rows)):
        errors.append("duplicate architecture verification test ID")
    references = set(REFERENCE.findall(matrix_text))
    for requirement in sorted(requirements - references):
        errors.append(f"uncovered requirement: {requirement}")
    for reference in sorted(references - requirements):
        errors.append(f"unknown requirement reference: {reference}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path("docs/testing/architecture-verification-matrix.md"),
    )
    parser.add_argument(
        "requirements",
        nargs="*",
        type=Path,
        default=[
            Path("docs/requirements/requirements-register.md"),
            Path("docs/requirements/subsystem-requirements.md"),
        ],
    )
    args = parser.parse_args()
    errors = validate(args.requirements, args.matrix)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
