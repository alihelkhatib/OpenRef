#!/usr/bin/env python3
"""Validate OpenRef audio benchmark evidence and optional promotion readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


COUNTERS = {
    "requested_blocks", "completed_blocks", "plc_calls", "encode_failures",
    "decode_failures", "process_failures", "deadline_misses",
    "maximum_encode_us", "maximum_render_us", "maximum_total_us",
    "average_encode_us", "average_render_us", "average_total_us",
    "stack_high_water_bytes", "stack_reserved_bytes", "static_memory_bytes",
    "memory_capacity_bytes", "clock_hz", "sample_rate_hz", "block_samples",
    "encoder_instances", "decoder_instances", "capture_dma_overruns",
    "playback_dma_underruns", "pacing_deadline_misses",
}
TEXT_FIELDS = {
    "target", "execution_mode", "compiler", "optimization", "codec",
    "firmware_commit", "sdk_version", "board_revision", "silicon_revision",
    "audio_io_mode",
}
CURRENT_FIELDS = {"idle_current_ma", "one_talker_current_ma", "six_talker_current_ma"}
ARTIFACT_KEYS = {"serial_log", "elf", "map"}


def validate_result(data: dict, require_promotion: bool = False) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != "openref-audio-benchmark-v2":
        errors.append("unsupported benchmark schema")
    for field in TEXT_FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{field} must be a nonempty string")
    for field in COUNTERS:
        value = data.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{field} must be a nonnegative integer")
    for field in ("complete", "passed"):
        if not isinstance(data.get(field), bool):
            errors.append(f"{field} must be boolean")
    for field in CURRENT_FIELDS:
        value = data.get(field)
        if value is not None and (not isinstance(value, (int, float)) or
                                  isinstance(value, bool) or value <= 0):
            errors.append(f"{field} must be null or positive")

    if errors:
        return errors
    compute_pass = (
        data["execution_mode"] == "paced-target" and
        data["audio_io_mode"] == "ping-pong-dma" and
        data["sample_rate_hz"] == 16000 and data["block_samples"] == 160 and
        data["encoder_instances"] == 1 and data["decoder_instances"] == 5 and
        data["requested_blocks"] >= 180000 and
        data["completed_blocks"] == data["requested_blocks"] and
        data["plc_calls"] > 0 and data["encode_failures"] == 0 and
        data["decode_failures"] == 0 and data["process_failures"] == 0 and
        data["deadline_misses"] == 0 and
        data["capture_dma_overruns"] == 0 and
        data["playback_dma_underruns"] == 0 and
        data["pacing_deadline_misses"] == 0 and
        data["maximum_total_us"] <= 8000 and
        data["complete"]
    )
    if data["passed"] != compute_pass:
        errors.append("passed does not match the controlled compute criteria")
    if require_promotion:
        if not compute_pass:
            errors.append("compute benchmark has not passed")
        if data["clock_hz"] <= 0 or data["stack_high_water_bytes"] <= 0:
            errors.append("promotion requires clock and stack evidence")
        if data["stack_reserved_bytes"] <= 0 or data["memory_capacity_bytes"] <= 0:
            errors.append("promotion requires reserved-stack and memory-capacity evidence")
        elif data["stack_high_water_bytes"] * 5 > data["stack_reserved_bytes"] * 4:
            errors.append("stack high-water exceeds the 80% promotion ceiling")
        used_memory = data["static_memory_bytes"] + data["stack_reserved_bytes"]
        if data["memory_capacity_bytes"] > 0 and used_memory * 5 > data["memory_capacity_bytes"] * 4:
            errors.append("static plus reserved-stack memory exceeds the 80% promotion ceiling")
        missing = sorted(field for field in CURRENT_FIELDS if data[field] is None)
        if missing:
            errors.append("promotion requires measured currents: " + ", ".join(missing))
        artifacts = data.get("artifact_sha256")
        if not isinstance(artifacts, dict) or set(artifacts) != ARTIFACT_KEYS or any(
            not isinstance(value, str) or len(value) != 64 or
            any(char not in "0123456789abcdefABCDEF" for char in value)
            for value in artifacts.values()
        ):
            errors.append("promotion requires SHA-256 evidence for serial_log, elf, and map")
        files = data.get("artifact_files")
        if not isinstance(files, dict) or set(files) != ARTIFACT_KEYS or any(
            not isinstance(value, str) or not value.strip() or
            Path(value).is_absolute() or ".." in Path(value).parts
            for value in files.values()
        ):
            errors.append("promotion requires safe relative filenames for serial_log, elf, and map")
    return errors


def validate_artifact_files(data: dict, artifact_root: Path) -> list[str]:
    """Verify promotion hashes against files under a bounded artifact root."""
    errors: list[str] = []
    files = data.get("artifact_files")
    hashes = data.get("artifact_sha256")
    if not isinstance(files, dict) or not isinstance(hashes, dict):
        return ["artifact filenames and hashes are required"]
    root = artifact_root.resolve()
    for key in sorted(ARTIFACT_KEYS):
        name = files.get(key)
        expected = hashes.get(key)
        if not isinstance(name, str):
            errors.append(f"artifact filename is missing: {key}")
            continue
        path = (root / name).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"artifact escapes the evidence root: {key}")
            continue
        if not path.is_file():
            errors.append(f"artifact file is missing: {key}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if not isinstance(expected, str) or actual.lower() != expected.lower():
            errors.append(f"artifact hash mismatch: {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("--require-promotion", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    data = json.loads(args.result.read_text(encoding="utf-8"))
    errors = validate_result(data, args.require_promotion)
    if args.require_promotion:
        if args.artifact_root is None:
            errors.append("promotion validation requires --artifact-root")
        else:
            errors.extend(validate_artifact_files(data, args.artifact_root))
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
