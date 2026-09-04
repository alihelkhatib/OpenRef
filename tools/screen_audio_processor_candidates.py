#!/usr/bin/env python3
"""Run the no-hardware OpenRef audio-processor admission screen.

This deliberately reports compile/footprint evidence only. It never converts a
cross-build into timing, power, or promotion evidence.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parents[1]
SOURCES = [
    "firmware/common/openref_audio_link.c",
    "firmware/audio_processor/common/openref_audio_capture.c",
    "firmware/audio_processor/common/openref_audio_playout.c",
    "firmware/audio_processor/common/openref_audio_mixer.c",
    "firmware/audio_processor/common/openref_audio_pipeline.c",
    "firmware/audio_processor/common/openref_audio_runtime.c",
    "firmware/audio_processor/benchmark/openref_audio_benchmark.c",
]
INCLUDES = [
    "firmware/common",
    "firmware/audio_processor/common",
    "firmware/audio_processor/benchmark",
]
PROFILES = {
    "mimxrt595-m33": ["-mcpu=cortex-m33", "-mthumb", "-mfloat-abi=soft"],
    "stm32h563-m33": ["-mcpu=cortex-m33", "-mthumb", "-mfloat-abi=soft"],
    # The portable C screen avoids assuming that LC3 has an MVE port. A vendor
    # run may add MVE/DSP flags and must record them in its result.
    "apollo510-portable": ["-mcpu=cortex-m55", "-mthumb", "-mfloat-abi=soft"],
}


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", default="arm-none-eabi-gcc")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/local/audio-candidate-screen")
    parser.add_argument("--profile", action="append", choices=sorted(PROFILES))
    args = parser.parse_args()
    compiler = shutil.which(args.compiler) or (args.compiler if Path(args.compiler).is_file() else None)
    if compiler is None:
        parser.error(f"compiler not found: {args.compiler}")

    profiles = args.profile or list(PROFILES)
    args.output.mkdir(parents=True, exist_ok=True)
    version = run([compiler, "--version"]).stdout.splitlines()[0]
    report = {
        "schema": "openref-audio-candidate-screen-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "cross-compile-and-object-footprint-only",
        "compiler": version,
        "promotion_evidence": False,
        "limitations": [
            "No target instructions were executed.",
            "No LC3 vendor library was linked.",
            "No timing, stack high-water, peripheral, or current claim is made.",
        ],
        "candidates": {},
    }
    common = ["-std=c11", "-Os", "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror"]
    include_flags = [flag for path in INCLUDES for flag in ("-I", str(ROOT / path))]
    for profile in profiles:
        profile_dir = args.output / profile
        profile_dir.mkdir(parents=True, exist_ok=True)
        objects = []
        errors = []
        for source in SOURCES:
            obj = profile_dir / (Path(source).stem + ".o")
            result = run([compiler, *common, *PROFILES[profile], *include_flags, "-c", str(ROOT / source), "-o", str(obj)])
            if result.returncode:
                errors.append({"source": source, "diagnostic": result.stderr.strip()})
            else:
                objects.append(obj)
        sizes = {"text": 0, "data": 0, "bss": 0}
        if not errors:
            sibling_size = Path(compiler).with_name("arm-none-eabi-size.exe" if Path(compiler).suffix else "arm-none-eabi-size")
            size_tool = str(sibling_size) if sibling_size.is_file() else (shutil.which("arm-none-eabi-size") or "arm-none-eabi-size")
            size_result = run([size_tool, "-A", *map(str, objects)])
            for line in size_result.stdout.splitlines():
                fields = line.split()
                if len(fields) >= 2:
                    section = fields[0]
                    try:
                        amount = int(fields[1])
                    except ValueError:
                        continue
                    if section.startswith(".text") or section in (".rodata", ".ARM.exidx"):
                        sizes["text"] += amount
                    elif section.startswith(".data"):
                        sizes["data"] += amount
                    elif section.startswith(".bss"):
                        sizes["bss"] += amount
        report["candidates"][profile] = {
            "compile_passed": not errors,
            "flags": common + PROFILES[profile],
            "portable_object_bytes": sizes if not errors else None,
            "errors": errors,
        }

    output = args.output / "screen-result.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0 if all(item["compile_passed"] for item in report["candidates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
