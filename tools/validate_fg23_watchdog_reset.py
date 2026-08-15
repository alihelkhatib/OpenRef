#!/usr/bin/env python3
"""Validate an FG23 injected-hang serial capture and watchdog attribution."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


HANG_RE = re.compile(
    r"\{\{\(openrefWatchdog\)\}\{Status:InjectedHang\}\{Feeds:(\d+)\}\}\}"
)
RESET_RE = re.compile(
    r"\{\{\(openrefReset\)\}\{Raw:0x([0-9a-fA-F]{8})\}"
    r"\{Classified:0x([0-9a-fA-F]{8})\}\{Watchdog:(0|1)\}\}\}"
)
RAW_WATCHDOG_MASK = 0x18
CLASSIFIED_WATCHDOG_MASK = 1 << 3


def validate_capture(text: str, expected_feeds: int | None = None) -> list[str]:
    errors: list[str] = []
    hangs = list(HANG_RE.finditer(text))
    resets = list(RESET_RE.finditer(text))
    if not hangs:
        return ["missing InjectedHang marker"]
    if expected_feeds is not None and not any(
        int(match.group(1)) == expected_feeds for match in hangs
    ):
        errors.append(f"no InjectedHang marker has Feeds:{expected_feeds}")

    attributed = []
    for reset in resets:
        raw = int(reset.group(1), 16)
        classified = int(reset.group(2), 16)
        watchdog_field = int(reset.group(3))
        if (
            raw & RAW_WATCHDOG_MASK
            and classified & CLASSIFIED_WATCHDOG_MASK
            and watchdog_field == 1
        ):
            attributed.append(reset)
    if not attributed:
        errors.append("missing reset with consistent raw and classified watchdog cause")
    elif not any(reset.start() > hang.start() for hang in hangs for reset in attributed):
        errors.append("watchdog-attributed reset does not follow an InjectedHang marker")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate OpenRef FG23 watchdog reset serial evidence"
    )
    parser.add_argument("capture", type=Path)
    parser.add_argument("--expected-feeds", type=int)
    args = parser.parse_args()
    if args.expected_feeds is not None and args.expected_feeds <= 0:
        parser.error("--expected-feeds must be greater than zero")
    errors = validate_capture(
        args.capture.read_text(encoding="utf-8", errors="replace"),
        args.expected_feeds,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("PASS: injected hang was followed by a consistently attributed watchdog reset")


if __name__ == "__main__":
    main()
