#!/usr/bin/env python3
"""Export an EDA-neutral FGM230SB symbol pin table from the controlled allocation."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from validate_fgm230_pin_allocation import validate_allocation


FIELDS = ("pin", "pad", "net", "direction", "safe_state", "class")


def export_pins(source: Path, output: Path) -> None:
    data = json.loads(source.read_text(encoding="utf-8"))
    errors = validate_allocation(data)
    if errors:
        raise ValueError("; ".join(errors))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for pin in sorted(data["pins"], key=lambda entry: entry["pin"]):
            writer.writerow({field: pin[field] for field in FIELDS})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export_pins(args.source, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
