#!/usr/bin/env python3
"""Validate an OpenRef audio-processor promotion benchmark result."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


EXPECTED = {
    "schema": "openref-audio-benchmark-v1",
    "benchmark_version": 1,
    "execution_mode": "paced-target",
    "sample_rate_hz": 16000,
    "channel_count": 1,
    "sample_format": "signed-16-bit-pcm",
    "frame_duration_us": 10000,
    "codec_frame_bytes": 40,
    "encoder_count": 1,
    "decoder_count": 5,
    "plc_period_packets": 97,
    "warmup_blocks": 1000,
    "requested_blocks": 180000,
    "processing_budget_us": 8000,
}

def expected_plc_calls() -> int:
    """Return PLC calls in the canonical measured block interval.

    Each packet supplies two blocks. Packet k's second block, 2*k + 1, is
    missing for source six when positive k is divisible by the PLC period.
    """
    interval = 2 * EXPECTED["plc_period_packets"]
    first_block = EXPECTED["warmup_blocks"]
    last_block = first_block + EXPECTED["requested_blocks"] - 1
    first_multiple = max(1, (first_block - 1 + interval - 1) // interval)
    last_multiple = (last_block - 1) // interval
    return max(0, last_multiple - first_multiple + 1)


EXPECTED_PLC_CALLS = expected_plc_calls()
EXPECTED_PACING_TICKS = EXPECTED["warmup_blocks"] + EXPECTED["requested_blocks"]
EXPECTED_ELAPSED_US = EXPECTED_PACING_TICKS * EXPECTED["frame_duration_us"]
PACING_ELAPSED_TOLERANCE_US = 1000

REQUIRED_TEXT = (
    "target",
    "silicon_revision",
    "compiler",
    "optimization",
    "codec",
    "firmware_commit",
    "memory_placement",
    "clock_configuration",
    "timer_source",
    "current_measurement",
)

REQUIRED_COUNTS = (
    "completed_blocks",
    "plc_calls",
    "encode_failures",
    "decode_failures",
    "process_failures",
    "deadline_misses",
    "maximum_encode_us",
    "maximum_render_us",
    "maximum_total_us",
    "average_encode_us",
    "average_render_us",
    "average_total_us",
    "stack_high_water_bytes",
    "pacing_ticks",
    "pacing_overruns",
    "elapsed_us",
)

PLACEHOLDER_TEXT = {"unknown", "not_measured", "n/a", "na", "none", "null", "tbd"}


def validate_result(result: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["root must be a JSON object"]
    for field, expected in EXPECTED.items():
        value = result.get(field)
        if type(value) is not type(expected) or value != expected:
            errors.append(f"{field} must equal {expected!r}")
    for field in REQUIRED_TEXT:
        if not isinstance(result.get(field), str) or not result[field].strip():
            errors.append(f"{field} must be a non-empty string")
        elif result[field].strip().lower() in PLACEHOLDER_TEXT:
            errors.append(f"{field} must not be placeholder provenance")
    if (not isinstance(result.get("clock_hz"), int) or
            isinstance(result.get("clock_hz"), bool) or result["clock_hz"] <= 0):
        errors.append("clock_hz must be a positive integer")
    for field in REQUIRED_COUNTS:
        if (not isinstance(result.get(field), int) or
                isinstance(result.get(field), bool) or result[field] < 0):
            errors.append(f"{field} must be a non-negative integer")
    for field in ("idle_current_ma", "one_talker_current_ma", "six_talker_current_ma"):
        value = result.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            errors.append(f"{field} must be a positive finite measurement")
    if result.get("complete") is not True:
        errors.append("complete must be true")
    if result.get("passed") is not True:
        errors.append("passed must be true")
    if (isinstance(result.get("completed_blocks"), int) and
            not isinstance(result["completed_blocks"], bool) and
            result["completed_blocks"] != 180000):
        errors.append("completed_blocks must equal 180000")
    if (isinstance(result.get("plc_calls"), int) and
            not isinstance(result["plc_calls"], bool) and
            result["plc_calls"] != EXPECTED_PLC_CALLS):
        errors.append(f"plc_calls must equal {EXPECTED_PLC_CALLS}")
    if isinstance(result.get("stack_high_water_bytes"), int) and \
            not isinstance(result["stack_high_water_bytes"], bool) and \
            result["stack_high_water_bytes"] <= 0:
        errors.append("stack_high_water_bytes must be positive")
    if (isinstance(result.get("pacing_ticks"), int) and
            not isinstance(result["pacing_ticks"], bool) and
            result["pacing_ticks"] != EXPECTED_PACING_TICKS):
        errors.append(f"pacing_ticks must equal {EXPECTED_PACING_TICKS}")
    if result.get("pacing_overruns") != 0:
        errors.append("pacing_overruns must equal 0")
    elapsed_us = result.get("elapsed_us")
    maximum_total = result.get("maximum_total_us")
    if (isinstance(elapsed_us, int) and not isinstance(elapsed_us, bool) and
            isinstance(maximum_total, int) and not isinstance(maximum_total, bool) and
            not EXPECTED_ELAPSED_US <= elapsed_us <= (
                EXPECTED_ELAPSED_US + maximum_total + PACING_ELAPSED_TOLERANCE_US
            )):
        errors.append(
            "elapsed_us must cover exactly the paced workload plus the final block and bounded interrupt latency"
        )
    for field in ("encode_failures", "decode_failures", "process_failures", "deadline_misses"):
        if result.get(field) != 0:
            errors.append(f"{field} must equal 0")
    maximum = result.get("maximum_total_us")
    if isinstance(maximum, int) and maximum > 8000:
        errors.append("maximum_total_us must be at most 8000")
    if isinstance(maximum, int) and not isinstance(maximum, bool) and maximum <= 0:
        errors.append("maximum_total_us must be positive")
    timing_pairs = (
        ("average_encode_us", "maximum_encode_us"),
        ("average_render_us", "maximum_render_us"),
        ("average_total_us", "maximum_total_us"),
    )
    for average_field, maximum_field in timing_pairs:
        average = result.get(average_field)
        maximum_value = result.get(maximum_field)
        if (isinstance(average, int) and not isinstance(average, bool) and
                isinstance(maximum_value, int) and not isinstance(maximum_value, bool) and
                average > maximum_value):
            errors.append(f"{average_field} must be at most {maximum_field}")
    average_total = result.get("average_total_us")
    average_encode = result.get("average_encode_us")
    average_render = result.get("average_render_us")
    if all(isinstance(value, int) and not isinstance(value, bool)
           for value in (average_total, average_encode, average_render)) and \
            not average_encode + average_render <= average_total <= average_encode + average_render + 1:
        errors.append(
            "average_total_us must be the sum of component averages, allowing one microsecond of truncation"
        )
    maximum_encode = result.get("maximum_encode_us")
    maximum_render = result.get("maximum_render_us")
    if all(isinstance(value, int) and not isinstance(value, bool)
           for value in (maximum, maximum_encode, maximum_render)) and \
            (maximum < maximum_encode or maximum < maximum_render):
        errors.append("maximum_total_us must cover encode and render maxima")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        result = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 2
    errors = validate_result(result)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"PASS {args.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
