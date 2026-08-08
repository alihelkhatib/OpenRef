from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from prototype0_fixture_readiness import analysis_command, command_text, validate


DEFAULT_FG23_ROOT = Path("firmware/prototype0/fg23")
DISCOVERABLE_GATES = {"E0-03", "E0-05", "E0-07"}
DISCOVERY_SKIP_FRAGMENTS = ("template", "example", "check", "run-report")
GPIO_TIME_COLUMNS = {"time_s", "time", "timestamp_s", "timestamp", "Time [s]", "Time"}
GPIO_CHANNEL_COLUMNS = {"channel", "Channel", "name", "Name"}
AUDIO_TIME_COLUMNS = {"time_us", "timestamp_us", "local_time_us", "time", "Time [s]", "Time"}
AUDIO_ID_COLUMNS = {"frame_id", "impulse_id", "sequence", "id"}
AUDIO_EVENT_COLUMNS = {"event", "marker", "name", "Event", "Marker"}
REPORT_SCHEMA = "prototype0-fixture-run-report-v1"


def _report_base(root: Path) -> dict[str, Any]:
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_posix(path: Path) -> str:
    return path.as_posix()


def _resolve_artifact_path(root: Path, command_path: str) -> Path:
    normalized = command_path.replace("\\", "/")
    root_prefix = DEFAULT_FG23_ROOT.as_posix() + "/"
    if normalized.startswith(root_prefix):
        return root / normalized[len(root_prefix):]
    if normalized.startswith("results/"):
        return root / normalized
    return Path(command_path)


def _artifact_argument_indexes(command: list[str]) -> tuple[list[int], int | None]:
    if len(command) < 3:
        return [], None
    analyzer = Path(command[1]).name
    if analyzer in {"analyze_scheduled_tx_gpio.py", "analyze_audio_loopback.py"}:
        input_indexes = [2]
    elif analyzer == "analyze_attenuation_sweep.py":
        input_indexes = []
        for index, item in enumerate(command[2:], start=2):
            if item.startswith("--"):
                break
            input_indexes.append(index)
    else:
        input_indexes = []

    json_index = None
    if "--json" in command:
        flag_index = command.index("--json")
        if flag_index + 1 < len(command):
            json_index = flag_index + 1
    return input_indexes, json_index


def rewrite_command_for_root(command: list[str], root: Path) -> list[str]:
    rewritten = list(command)
    if rewritten and rewritten[0] == "python":
        rewritten[0] = sys.executable
    input_indexes, json_index = _artifact_argument_indexes(rewritten)
    for index in input_indexes:
        rewritten[index] = _as_posix(_resolve_artifact_path(root, rewritten[index]))
    if json_index is not None:
        rewritten[json_index] = _as_posix(_resolve_artifact_path(root, rewritten[json_index]))
    return rewritten


def _input_status(command: list[str]) -> list[dict[str, Any]]:
    input_indexes, _ = _artifact_argument_indexes(command)
    return [
        _file_artifact(Path(command[index]))
        for index in input_indexes
    ]


def _json_output_path(command: list[str]) -> Path | None:
    _, json_index = _artifact_argument_indexes(command)
    if json_index is None:
        return None
    return Path(command[json_index])


def _file_artifact(path: Path) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "bytes": None,
        "sha256": None,
        "mtime_utc": None,
    }
    if not path.exists():
        return artifact
    raw = path.read_bytes()
    artifact["bytes"] = len(raw)
    artifact["sha256"] = hashlib.sha256(raw).hexdigest()
    artifact["mtime_utc"] = datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=timezone.utc,
    ).isoformat()
    return artifact


def _summary_passes(summary: Any) -> bool:
    if not isinstance(summary, dict):
        return False
    if "pass" in summary:
        return summary["pass"] is True
    if "passed" in summary:
        return summary["passed"] is True
    return False


def _csv_fieldnames(path: Path) -> tuple[list[str], int]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), len(rows)


def _fixture_input_contract_failures(
    gate: str,
    metadata: dict[str, Any],
    command: list[str],
) -> list[str]:
    input_indexes, _ = _artifact_argument_indexes(command)
    input_paths = [Path(command[index]) for index in input_indexes]
    failures: list[str] = []
    if gate == "E0-03" and input_paths:
        path = input_paths[0]
        fieldnames, row_count = _csv_fieldnames(path)
        fields = set(fieldnames)
        channels = metadata.get("channels", {})
        queue = channels.get("queue", "PB3") if isinstance(channels, dict) else "PB3"
        start = channels.get("start", "PB2") if isinstance(channels, dict) else "PB2"
        has_time = bool(fields & GPIO_TIME_COLUMNS)
        has_edge_channels = bool(fields & GPIO_CHANNEL_COLUMNS)
        has_sampled_channels = queue in fields and start in fields
        if row_count == 0:
            failures.append(f"{path}: CSV has no data rows")
        if not has_time:
            failures.append(f"{path}: CSV missing recognizable time column")
        if not has_edge_channels and not has_sampled_channels:
            failures.append(
                f"{path}: CSV must be edge-list with a channel column or sampled columns {queue}/{start}"
            )
    elif gate == "E0-05":
        expected_packets = metadata.get("packet_count_per_step")
        try:
            minimum_packets = int(expected_packets)
        except (TypeError, ValueError):
            minimum_packets = 0
        for path in input_paths:
            try:
                data = _load_json(path)
            except json.JSONDecodeError:
                failures.append(f"{path}: packet summary JSON is invalid")
                continue
            summaries = data if isinstance(data, list) else [data]
            if not summaries or not all(isinstance(item, dict) for item in summaries):
                failures.append(f"{path}: packet summary must be an object or list of objects")
                continue
            for index, item in enumerate(summaries):
                label = f"{path}[{index}]"
                transmitted = item.get("transmitted_packets")
                requested = item.get("requested_packets")
                rx_count = item.get("rx_count")
                if transmitted in (None, ""):
                    failures.append(f"{label}: transmitted_packets is required")
                if rx_count in (None, ""):
                    failures.append(f"{label}: rx_count is required")
                for key, value in (
                    ("requested_packets", requested),
                    ("transmitted_packets", transmitted),
                ):
                    if value in (None, ""):
                        continue
                    try:
                        packet_count = int(value)
                    except (TypeError, ValueError):
                        failures.append(f"{label}: {key} must be an integer")
                        continue
                    if minimum_packets and packet_count < minimum_packets:
                        failures.append(
                            f"{label}: {key} {packet_count} below required {minimum_packets}"
                        )
    elif gate == "E0-07" and input_paths:
        path = input_paths[0]
        fieldnames, row_count = _csv_fieldnames(path)
        fields = set(fieldnames)
        if row_count == 0:
            failures.append(f"{path}: CSV has no data rows")
        if not fields & AUDIO_TIME_COLUMNS:
            failures.append(f"{path}: CSV missing recognizable time column")
        if not fields & AUDIO_ID_COLUMNS:
            failures.append(f"{path}: CSV missing recognizable frame/id column")
        if not fields & AUDIO_EVENT_COLUMNS:
            failures.append(f"{path}: CSV missing recognizable event column")
    return failures


def discover_readiness(root: Path, gate: str) -> Path | None:
    if gate not in DISCOVERABLE_GATES:
        raise ValueError(f"unsupported gate for discovery: {gate}")
    gate_token = gate.lower()
    candidates = []
    for path in (root / "results").glob(f"*-{gate_token}-readiness*.json"):
        lower_name = path.name.lower()
        if any(fragment in lower_name for fragment in DISCOVERY_SKIP_FRAGMENTS):
            continue
        candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def run(readiness_path: Path, *, root: Path, dry_run: bool = False) -> dict[str, Any]:
    metadata = _load_json(readiness_path)
    if not isinstance(metadata, dict):
        return {
            **_report_base(root),
            "pass": False,
        "status": "invalid-readiness",
        "readiness": str(readiness_path),
        "readiness_artifact": _file_artifact(readiness_path),
        "failures": ["readiness metadata is not a JSON object"],
    }
    gate = str(metadata.get("gate", ""))
    failures = validate(gate, metadata)
    if failures:
        return {
            **_report_base(root),
            "pass": False,
            "status": "not-ready",
            "gate": gate,
            "readiness": str(readiness_path),
            "readiness_artifact": _file_artifact(readiness_path),
            "failures": failures,
        }

    command = analysis_command(gate, metadata) or []
    rewritten = rewrite_command_for_root(command, root)
    inputs = _input_status(rewritten)
    missing_inputs = [item["path"] for item in inputs if not item["exists"]]
    output_path = _json_output_path(rewritten)
    report: dict[str, Any] = {
        **_report_base(root),
        "pass": False,
        "status": "dry-run" if dry_run else "pending",
        "gate": gate,
        "readiness": str(readiness_path),
        "readiness_artifact": _file_artifact(readiness_path),
        "analysis_command": rewritten,
        "analysis_command_text": command_text(rewritten),
        "inputs": inputs,
        "summary_json": str(output_path) if output_path is not None else None,
        "summary_artifact": _file_artifact(output_path) if output_path is not None else None,
    }
    if dry_run:
        return report
    if missing_inputs:
        report["status"] = "missing-inputs"
        report["failures"] = ["missing input: " + path for path in missing_inputs]
        return report
    contract_failures = _fixture_input_contract_failures(gate, metadata, rewritten)
    if contract_failures:
        report["status"] = "invalid-inputs"
        report["failures"] = contract_failures
        return report

    completed = subprocess.run(rewritten, capture_output=True, text=True)
    report["returncode"] = completed.returncode
    report["stdout"] = completed.stdout
    report["stderr"] = completed.stderr
    failures = []
    summary = None
    if output_path is not None and output_path.exists():
        try:
            summary = _load_json(output_path)
            report["summary"] = summary
            report["summary_artifact"] = _file_artifact(output_path)
        except json.JSONDecodeError:
            report["summary_artifact"] = _file_artifact(output_path)
            report["summary_error"] = "summary JSON is invalid"
            failures.append("summary JSON is invalid")
    elif output_path is not None:
        failures.append(f"summary JSON missing: {output_path}")
    if summary is not None and not _summary_passes(summary):
        failures.append("summary JSON did not report pass:true")
    if completed.returncode != 0:
        failures.append(f"analyzer exited {completed.returncode}")
    report["failures"] = failures
    report["pass"] = not failures
    report["status"] = "passed" if report["pass"] else "failed"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a Prototype 0 fixture analyzer from readiness metadata."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--readiness", type=Path)
    source.add_argument(
        "--gate",
        choices=sorted(DISCOVERABLE_GATES),
        help="discover the newest real readiness file for this gate under ROOT/results",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_FG23_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    readiness = args.readiness
    if readiness is None:
        readiness = discover_readiness(args.root, args.gate)
        if readiness is None:
            report = {
                **_report_base(args.root),
                "pass": False,
                "status": "no-readiness",
                "gate": args.gate,
                "failures": [
                    f"no live readiness file found under {args.root / 'results'}"
                ],
            }
            rendered = json.dumps(report, indent=2, sort_keys=True)
            print(rendered)
            if args.json is not None:
                args.json.parent.mkdir(parents=True, exist_ok=True)
                args.json.write_text(rendered + "\n", encoding="utf-8")
            raise SystemExit(1)

    report = run(readiness, root=args.root, dry_run=args.dry_run)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(0 if report["pass"] or report["status"] == "dry-run" else 1)


if __name__ == "__main__":
    main()
