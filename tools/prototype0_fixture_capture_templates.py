from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


DEFAULT_OUTPUT_DIR = Path("firmware/prototype0/fg23/templates/fixture-captures")
SUPPORTED_GATES = ("E0-03", "E0-05", "E0-07")


CAPTURE_TEMPLATES: dict[str, tuple[tuple[str, str], ...]] = {
    "E0-03": (
        (
            "e0-03-scheduled-tx-gpio-template.csv",
            "\n".join(
                [
                    "Time [s],Channel,Value",
                    "0.000100,PB3,1",
                    "0.000101,PB3,0",
                    "0.000104,PB2,1",
                    "0.000105,PB2,0",
                    "0.000200,PB3,1",
                    "0.000201,PB3,0",
                    "0.000204,PB2,1",
                    "0.000205,PB2,0",
                ]
            )
            + "\n",
        ),
    ),
    "E0-05": (
        (
            "e0-05-step-00-baseline-template.json",
            json.dumps(
                {
                    "label": "baseline",
                    "rx_port": "COM8",
                    "tx_port": "COM10",
                    "rf_path": 0,
                    "physical_setting": "no attenuator or baseline shield setting",
                    "requested_packets": 200,
                    "transmitted_packets": 200,
                    "rx_count": "REPLACE_WITH_MEASURED_RX_COUNT",
                    "rx_crc_drop": "REPLACE_WITH_MEASURED_CRC_DROPS",
                    "delivery_ratio": "REPLACE_WITH_RX_COUNT_DIVIDED_BY_TRANSMITTED",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
        ),
        (
            "e0-05-step-01-30db-template.json",
            json.dumps(
                {
                    "label": "30dB",
                    "rx_port": "COM8",
                    "tx_port": "COM10",
                    "rf_path": 0,
                    "physical_setting": "30 dB inline attenuator or repeatable shielded setting",
                    "requested_packets": 200,
                    "transmitted_packets": 200,
                    "rx_count": "REPLACE_WITH_MEASURED_RX_COUNT",
                    "rx_crc_drop": "REPLACE_WITH_MEASURED_CRC_DROPS",
                    "delivery_ratio": "REPLACE_WITH_RX_COUNT_DIVIDED_BY_TRANSMITTED",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
        ),
    ),
    "E0-07": (
        (
            "e0-07-audio-loopback-template.csv",
            "\n".join(
                [
                    "frame_id,event,time_us",
                    "1,impulse,0",
                    "1,capture_frame,10000",
                    "1,packet_queue,30000",
                    "1,tx_start,35000",
                    "1,rx_done,60000",
                    "1,playback_output,90000",
                ]
            )
            + "\n",
        ),
    ),
}


def gates_from_arg(gate: str) -> tuple[str, ...]:
    if gate == "all":
        return SUPPORTED_GATES
    return (gate,)


def template_entries(gate: str) -> tuple[tuple[str, str], ...]:
    if gate not in CAPTURE_TEMPLATES:
        raise ValueError(f"unsupported gate {gate}")
    return CAPTURE_TEMPLATES[gate]


def write_capture_templates(
    gates: Iterable[str],
    output_dir: Path,
    *,
    force: bool = False,
) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, object]] = []
    for gate in gates:
        for filename, content in template_entries(gate):
            path = output_dir / filename
            if path.exists() and not force:
                written.append(
                    {
                        "gate": gate,
                        "path": str(path),
                        "written": False,
                        "reason": "exists",
                    }
                )
                continue
            path.write_text(content, encoding="utf-8", newline="\n")
            written.append(
                {
                    "gate": gate,
                    "path": str(path),
                    "written": True,
                    "bytes": len(content.encode("utf-8")),
                }
            )
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write non-passing example capture-file templates for Prototype 0 fixture gates."
    )
    parser.add_argument("--gate", choices=("all", *SUPPORTED_GATES), default="all")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    result = {
        "pass": True,
        "gate": args.gate,
        "output_dir": str(args.output_dir),
        "templates": write_capture_templates(
            gates_from_arg(args.gate),
            args.output_dir,
            force=args.force,
        ),
        "note": "Templates show accepted file shape only; they are intentionally insufficient or placeholder-filled and must not be used as passing fixture evidence.",
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
