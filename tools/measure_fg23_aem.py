#!/usr/bin/env python3
"""Capture repeatable average-current measurements from FG23 kit AEMs."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


def parse_board(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("board must be NAME=DEBUG_SERIAL")
    name, serial = value.split("=", 1)
    if not name or not serial.isdigit():
        raise argparse.ArgumentTypeError("board must be NAME=DEBUG_SERIAL")
    return name, serial


def measure(
    commander: Path,
    boards: Sequence[tuple[str, str]],
    window_ms: int,
) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for name, serial in boards:
        command = [
            str(commander), "aem", "measure", "--windowlength", str(window_ms),
            "--serialno", serial, "--json",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        try:
            response = json.loads(completed.stdout)
        except json.JSONDecodeError:
            response = {"success": False, "error": [completed.stderr.strip()]}
        results.append({
            "name": name,
            "debug_serial": serial,
            "returncode": completed.returncode,
            "response": response,
        })
    return {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "window_ms": window_ms,
        "boards": results,
        "all_succeeded": all(
            item["returncode"] == 0 and item["response"].get("success", False)
            for item in results
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure FG23 kit AEM current")
    parser.add_argument("--commander", required=True, type=Path)
    parser.add_argument("--board", action="append", type=parse_board, required=True)
    parser.add_argument("--window-ms", type=int, default=10_000)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.window_ms <= 0:
        parser.error("--window-ms must be positive")
    result = measure(args.commander, args.board, args.window_ms)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["all_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

