#!/usr/bin/env python3
"""Extract one OpenRef benchmark JSON object from a raw serial log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "openref-audio-benchmark-v1"


def extract_result(text: str) -> dict:
    matches = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("schema") == SCHEMA:
            matches.append((line_number, value))
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one {SCHEMA} object, found {len(matches)}"
        )
    return matches[0][1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = extract_result(args.log.read_text(encoding="utf-8", errors="replace"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1
    print(f"EXTRACTED {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
