from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from prototype0_fixture_actions import concrete_next_actions
from prototype0_fixture_readiness import analysis_command, command_text, validate


DEFAULT_FG23_ROOT = Path("firmware/prototype0/fg23")
DEFAULT_ROLLUP_DOC = "20260807-prototype0-gate-status.md"
FIXTURE_RUN_REPORT_SCHEMA = "prototype0-fixture-run-report-v1"


@dataclass(frozen=True)
class Evidence:
    path: str
    kind: str = "doc"
    expect_pass: bool = False
    validator: str | None = None


@dataclass(frozen=True)
class Gate:
    gate_id: str
    name: str
    target_status: str
    evidence: tuple[Evidence, ...]
    blockers: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()


GATES: tuple[Gate, ...] = (
    Gate(
        "E0-01",
        "Toolchain reproduction",
        "passed",
        (
            Evidence("20260807-e0-01-link-smoke-result.md"),
            Evidence("20260808-railtest-bidirectional-retention-result.md"),
            Evidence("results/20260807-node-1-e0-01.log"),
            Evidence("results/20260807-node-2-e0-01.log"),
            Evidence(
                "results/20260808-railtest-bidirectional-retention-summary.json",
                "json",
                True,
                "railtest_bidirectional_retention",
            ),
            Evidence(
                "results/20260808-railtest-bidirectional-retention-1000-summary.json",
                "json",
                True,
                "railtest_bidirectional_retention",
            ),
        ),
    ),
    Gate(
        "E0-02",
        "Continuous packet pair",
        "passed",
        (
            Evidence("20260807-railtest-packet-precheck-result.md"),
            Evidence("20260807-railtest-1500pkt-20ms-result.md"),
            Evidence("20260807-openref-railtest-wire-format-result.md"),
            Evidence("20260807-openref-app-hook-result.md"),
            Evidence("20260807-openref-autotx-result.md"),
            Evidence("20260807-openref-autorx-result.md"),
            Evidence("20260807-openref-autorole-result.md"),
            Evidence("results/20260807-openref-autorole-1hour-com8-rx-summary.json", "json", True),
        ),
    ),
    Gate(
        "E0-03",
        "Scheduled transmission",
        "partial",
        (
            Evidence("20260807-railtest-scheduled-tx-precheck-result.md"),
            Evidence("20260807-openref-scheduled-tx-sdk-result.md"),
            Evidence("20260807-openref-scheduled-tx-gpio-marker-plan.md"),
            Evidence("results/20260807-openref-scheduled-tx-com8-summary.json", "json", True),
        ),
        ("External GPIO/logic-analyzer or oscilloscope capture is still required.",),
        (
            "python tools/prototype0_fixture_readiness.py --gate E0-03 --template --json firmware/prototype0/fg23/results/YYYYMMDD-e0-03-readiness.json",
            "python tools/prototype0_fixture_readiness.py --gate E0-03 --check firmware/prototype0/fg23/results/YYYYMMDD-e0-03-readiness.json",
            "python tools/run_prototype0_fixture_analysis.py --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-03-readiness.json --dry-run",
            "python tools/run_prototype0_fixture_analysis.py --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-03-readiness.json --json firmware/prototype0/fg23/results/YYYYMMDD-e0-03-run-report.json",
            "python tools/run_prototype0_fixture_analysis.py --gate E0-03 --dry-run",
            "python tools/run_prototype0_fixture_analysis.py --gate E0-03 --json firmware/prototype0/fg23/results/YYYYMMDD-e0-03-run-report.json",
        ),
    ),
    Gate(
        "E0-04",
        "Payload capacity sweep",
        "passed",
        (
            Evidence("20260807-railtest-capacity-precheck-result.md"),
            Evidence("20260807-openref-runtime-capacity-result.md"),
            Evidence("results/20260807-openref-autorole-capacity-sweep-summary.json", "json", True),
        ),
    ),
    Gate(
        "E0-05",
        "Controlled attenuation",
        "blocked",
        (
            Evidence("20260807-openref-attenuation-analysis-plan.md"),
            Evidence("20260808-railtest-tx-power-sweep-precheck-result.md"),
            Evidence("results/20260808-railtest-tx-power-sweep-com8-rx-analysis.json", "json", True),
            Evidence("results/20260808-railtest-tx-power-sweep-com10-rx-analysis.json", "json", True),
            Evidence("20260808-railtest-rssi-path0-precheck-result.md"),
            Evidence("results/20260808-railtest-rssi-com8-rx-com10-tx-rf0-summary.json", "json", True),
            Evidence("results/20260808-railtest-rssi-com10-rx-com8-tx-rf0-summary.json", "json", True),
            Evidence("20260808-railtest-rssi-path1-negative-precheck-result.md"),
            Evidence("results/20260808-railtest-rssi-com8-rx-com10-tx-rf1-summary.json", "json", True),
            Evidence("results/20260808-railtest-rssi-com10-rx-com8-tx-rf1-summary.json", "json", True),
        ),
        ("Controlled RF attenuation, shield box, or repeatable shielding setup is still required.",),
        (
            "python tools/prototype0_fixture_readiness.py --gate E0-05 --template --json firmware/prototype0/fg23/results/YYYYMMDD-e0-05-readiness.json",
            "python tools/prototype0_fixture_readiness.py --gate E0-05 --check firmware/prototype0/fg23/results/YYYYMMDD-e0-05-readiness.json",
            "python tools/run_prototype0_fixture_analysis.py --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-05-readiness.json --dry-run",
            "python tools/run_prototype0_fixture_analysis.py --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-05-readiness.json --json firmware/prototype0/fg23/results/YYYYMMDD-e0-05-run-report.json",
            "python tools/run_prototype0_fixture_analysis.py --gate E0-05 --dry-run",
            "python tools/run_prototype0_fixture_analysis.py --gate E0-05 --json firmware/prototype0/fg23/results/YYYYMMDD-e0-05-run-report.json",
        ),
    ),
    Gate(
        "E0-06",
        "Radio fault recovery",
        "passed",
        (
            Evidence("20260807-railtest-fault-precheck-result.md"),
            Evidence("20260807-openref-recovery-precheck-result.md"),
            Evidence("20260807-openref-malformed-rx-result.md"),
            Evidence("20260807-openref-queue-pressure-result.md"),
            Evidence("20260807-openref-forced-reset-result.md"),
            Evidence("20260808-railtest-rx-overflow-reset-recovery-result.md"),
            Evidence("20260807-openref-memory-watermark-result.md"),
            Evidence("results/20260808-railtest-rx-overflow-reset-recovery-com8-summary.json", "json", True),
            Evidence("results/20260808-railtest-rx-overflow-reset-recovery-com10-summary.json", "json", True),
        ),
    ),
    Gate(
        "E0-07",
        "Audio loopback timing",
        "blocked",
        (
            Evidence("20260807-openref-audio-loopback-analysis-plan.md"),
        ),
        ("Audio capture/playback fixture and firmware timing markers are still required.",),
        (
            "python tools/prototype0_fixture_readiness.py --gate E0-07 --template --json firmware/prototype0/fg23/results/YYYYMMDD-e0-07-readiness.json",
            "python tools/prototype0_fixture_readiness.py --gate E0-07 --check firmware/prototype0/fg23/results/YYYYMMDD-e0-07-readiness.json",
            "python tools/run_prototype0_fixture_analysis.py --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-07-readiness.json --dry-run",
            "python tools/run_prototype0_fixture_analysis.py --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-07-readiness.json --json firmware/prototype0/fg23/results/YYYYMMDD-e0-07-run-report.json",
            "python tools/run_prototype0_fixture_analysis.py --gate E0-07 --dry-run",
            "python tools/run_prototype0_fixture_analysis.py --gate E0-07 --json firmware/prototype0/fg23/results/YYYYMMDD-e0-07-run-report.json",
        ),
    ),
)


def _load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _json_passes(data: Any) -> bool:
    if isinstance(data, dict):
        if "pass" in data:
            return data["pass"] is True
        if "passed" in data:
            return data["passed"] is True
    if isinstance(data, list):
        return bool(data) and all(_json_passes(item) for item in data)
    return False


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _validate_retention_summary(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["retention summary must be a JSON object"]

    failures: list[str] = []
    if data.get("pass") is not True:
        failures.append("retention summary pass must be true")

    expected_packets = _as_int(data.get("packets"))
    directions = data.get("directions")
    if not isinstance(directions, list) or len(directions) != 2:
        failures.append("retention summary must contain exactly two directions")
        return failures

    seen_pairs: set[tuple[str, str]] = set()
    for index, direction in enumerate(directions):
        prefix = f"directions[{index}]"
        if not isinstance(direction, dict):
            failures.append(f"{prefix} must be a JSON object")
            continue
        if direction.get("pass") is not True:
            failures.append(f"{prefix}.pass must be true")

        summary = direction.get("summary")
        if not isinstance(summary, dict):
            failures.append(f"{prefix}.summary must be a JSON object")
            continue

        tx_port = direction.get("tx_port") or summary.get("tx_port")
        rx_port = direction.get("rx_port") or summary.get("rx_port")
        if isinstance(tx_port, str) and isinstance(rx_port, str):
            seen_pairs.add((tx_port, rx_port))
        else:
            failures.append(f"{prefix} must include tx_port and rx_port")

        direction_expected = expected_packets or _as_int(summary.get("requested_packets"))
        if direction_expected is None:
            failures.append(f"{prefix}.summary requested packet count is missing")
            continue

        for key in ("requested_packets", "transmitted_packets", "rx_count", "sync_detect"):
            value = _as_int(summary.get(key))
            if value != direction_expected:
                failures.append(f"{prefix}.summary.{key} expected {direction_expected}, got {summary.get(key)!r}")

        for key in ("rx_crc_drop", "tx_failed_packets"):
            value = _as_int(summary.get(key))
            if value != 0:
                failures.append(f"{prefix}.summary.{key} expected 0, got {summary.get(key)!r}")

        ratio = summary.get("delivery_ratio")
        if not isinstance(ratio, (int, float)) or float(ratio) != 1.0:
            failures.append(f"{prefix}.summary.delivery_ratio expected 1.0, got {ratio!r}")

    if len(seen_pairs) != 2:
        failures.append("retention summary must cover two distinct TX/RX directions")
    if len({tx for tx, _rx in seen_pairs}) < 2 or len({rx for _tx, rx in seen_pairs}) < 2:
        failures.append("retention summary must exercise both boards as TX and RX")
    return failures


def _json_validation_failures(data: Any, validator: str | None) -> list[str]:
    if validator is None:
        return [] if _json_passes(data) else ["pass field not true"]
    if validator == "railtest_bidirectional_retention":
        return _validate_retention_summary(data)
    return [f"unknown JSON evidence validator {validator!r}"]


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _rollup_reference_name(path: str) -> str:
    return Path(path).name


STOP_TERMS = {
    "and",
    "are",
    "before",
    "box",
    "can",
    "external",
    "for",
    "is",
    "or",
    "required",
    "requires",
    "setup",
    "still",
    "the",
}


def _significant_terms(text: str) -> set[str]:
    normalized = re.sub(r"`[^`]+`", " ", text.lower())
    terms = set()
    for token in re.findall(r"[a-z0-9]+", normalized):
        if len(token) < 4 or token in STOP_TERMS:
            continue
        if token.startswith("attenuat"):
            token = "attenuat"
        elif token.startswith("shield"):
            token = "shield"
        terms.add(token)
    return {
        token
        for token in terms
        if len(token) >= 4 and token not in STOP_TERMS
    }


def _blocker_represented(blocker: str, rollup_text: str | None) -> bool:
    if rollup_text is None:
        return False
    blocker_terms = _significant_terms(blocker)
    rollup_terms = _significant_terms(rollup_text)
    if not blocker_terms:
        return True
    return len(blocker_terms & rollup_terms) >= min(2, len(blocker_terms))


def _resolve_command_path(root_path: Path, command_path: str) -> Path:
    normalized = command_path.replace("\\", "/")
    root_prefix = DEFAULT_FG23_ROOT.as_posix() + "/"
    if normalized.startswith(root_prefix):
        return root_path / normalized[len(root_prefix):]
    if normalized.startswith("results/"):
        return root_path / normalized
    return Path(command_path)


def _relative_to_root(root_path: Path, path: Path) -> str:
    try:
        return path.relative_to(root_path).as_posix()
    except ValueError:
        return path.as_posix()


def _command_analysis_inputs(command: list[str]) -> list[str]:
    if len(command) < 3:
        return []
    analyzer = Path(command[1]).name
    if analyzer in {"analyze_scheduled_tx_gpio.py", "analyze_audio_loopback.py"}:
        return [command[2]]
    if analyzer == "analyze_attenuation_sweep.py":
        inputs: list[str] = []
        for item in command[2:]:
            if item.startswith("--"):
                break
            inputs.append(item)
        return inputs
    return []


def _command_json_output(command: list[str]) -> str | None:
    if "--json" not in command:
        return None
    index = command.index("--json")
    if index + 1 >= len(command):
        return None
    return command[index + 1]


def _analysis_artifacts(root_path: Path, command: list[str]) -> dict[str, Any]:
    inputs = []
    for item in _command_analysis_inputs(command):
        path = _resolve_command_path(root_path, item)
        inputs.append(
            {
                "path": _relative_to_root(root_path, path),
                "exists": path.exists(),
            }
        )

    output_item = _command_json_output(command)
    summary = None
    if output_item is not None:
        path = _resolve_command_path(root_path, output_item)
        data = _load_json(path) if path.exists() else None
        summary = {
            "path": _relative_to_root(root_path, path),
            "exists": path.exists(),
            "json_valid": data is not None if path.exists() else None,
            "pass": _json_passes(data) if data is not None else None,
        }

    return {
        "inputs": inputs,
        "inputs_present": sum(1 for item in inputs if item["exists"]),
        "inputs_total": len(inputs),
        "summary": summary,
    }


def _latest_readiness(root_path: Path, gate_id: str) -> dict[str, Any]:
    pattern = f"*-{gate_id.lower()}-readiness*.json"
    candidates = sorted(
        (root_path / "results").glob(pattern),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    if not candidates:
        return {
            "status": "missing",
            "path": None,
            "failures": ["no readiness metadata found"],
        }

    path = candidates[0]
    relative_path = path.relative_to(root_path).as_posix()
    data = _load_json(path)
    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "path": relative_path,
            "failures": ["readiness metadata is not a JSON object"],
        }

    failures = validate(gate_id, data)
    result: dict[str, Any] = {
        "status": "ready" if not failures else "not-ready",
        "path": relative_path,
        "failures": failures,
    }
    if not failures:
        command = analysis_command(gate_id, data)
        result["analysis_command"] = command
        result["analysis_command_text"] = command_text(command or [])
        result["analysis_artifacts"] = _analysis_artifacts(root_path, command or [])
    return result


def _latest_run_report(root_path: Path, gate_id: str) -> dict[str, Any]:
    pattern = f"*-{gate_id.lower()}-run-report*.json"
    candidates = sorted(
        (root_path / "results").glob(pattern),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    if not candidates:
        return {
            "status": "missing",
            "path": None,
            "failures": ["no fixture runner report found"],
        }

    path = candidates[0]
    relative_path = path.relative_to(root_path).as_posix()
    data = _load_json(path)
    if not isinstance(data, dict):
        return {
            "status": "invalid",
            "path": relative_path,
            "failures": ["fixture runner report is not a JSON object"],
        }

    status = str(data.get("status", "unknown"))
    passed = data.get("pass") is True
    failures = data.get("failures", [])
    if not isinstance(failures, list):
        failures = ["fixture runner failures field is not a list"]
    return {
        "status": "passed" if passed else status,
        "path": relative_path,
        "schema": data.get("schema"),
        "generated_at": data.get("generated_at"),
        "root": data.get("root"),
        "pass": passed,
        "gate": data.get("gate"),
        "readiness": data.get("readiness"),
        "readiness_artifact": data.get("readiness_artifact"),
        "inputs": data.get("inputs"),
        "summary_json": data.get("summary_json"),
        "summary_artifact": data.get("summary_artifact"),
        "failures": failures,
    }


def _resolve_artifact_path(root_path: Path, artifact_path: str) -> Path:
    normalized = artifact_path.replace("\\", "/")
    root_prefix = DEFAULT_FG23_ROOT.as_posix() + "/"
    if normalized.startswith(root_prefix):
        return root_path / normalized[len(root_prefix):]
    if normalized.startswith("results/"):
        return root_path / normalized
    return Path(artifact_path)


def _artifact_integrity_failures(
    root_path: Path,
    prefix: str,
    artifact: dict[str, Any],
) -> list[str]:
    path_text = artifact.get("path")
    if not isinstance(path_text, str) or not path_text:
        return []
    path = _resolve_artifact_path(root_path, path_text)
    if not path.exists():
        return []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"{prefix} cannot be read: {exc}"]

    failures = []
    if isinstance(artifact.get("bytes"), int) and artifact.get("bytes") != len(raw):
        failures.append(
            f"{prefix}.bytes does not match current file: "
            f"{artifact.get('bytes')} != {len(raw)}"
        )
    sha256 = artifact.get("sha256")
    current_sha256 = hashlib.sha256(raw).hexdigest()
    if isinstance(sha256, str) and len(sha256) == 64 and sha256 != current_sha256:
        failures.append(f"{prefix}.sha256 does not match current file")
    return failures


def _resolved_artifact_identity(root_path: Path, artifact_path: str) -> str:
    return str(_resolve_artifact_path(root_path, artifact_path).resolve())


def _readiness_promotion_failures(
    root_path: Path,
    gate_id: str,
    run_report: dict[str, Any],
) -> list[str]:
    readiness = run_report.get("readiness")
    if not isinstance(readiness, str) or not readiness:
        return ["run report readiness is missing"]

    readiness_artifact = run_report.get("readiness_artifact")
    if not isinstance(readiness_artifact, dict):
        failures = ["run report readiness_artifact is missing"]
    else:
        failures = []
        if readiness_artifact.get("exists") is not True:
            failures.append("run report readiness_artifact does not exist")
        if readiness_artifact.get("path") != readiness:
            failures.append("run report readiness_artifact path does not match readiness")
        if not isinstance(readiness_artifact.get("bytes"), int) or readiness_artifact.get("bytes") <= 0:
            failures.append("run report readiness_artifact.bytes is missing")
        sha256 = readiness_artifact.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            failures.append("run report readiness_artifact.sha256 is missing")
        failures.extend(
            _artifact_integrity_failures(
                root_path,
                "run report readiness_artifact",
                readiness_artifact,
            )
        )

    readiness_path = _resolve_artifact_path(root_path, readiness)
    if not readiness_path.exists():
        return failures + [f"run report readiness missing: {readiness}"]

    metadata = _load_json(readiness_path)
    if not isinstance(metadata, dict):
        return failures + [f"run report readiness invalid JSON object: {readiness}"]

    failures.extend(
        f"run report readiness invalid: {failure}"
        for failure in validate(gate_id, metadata)
    )
    command = analysis_command(gate_id, metadata)
    if not command:
        failures.append("run report readiness does not produce an analyzer command")
        return failures

    expected_inputs = [
        _resolved_artifact_identity(root_path, item)
        for item in _command_analysis_inputs(command)
    ]
    actual_inputs = [
        _resolved_artifact_identity(root_path, artifact["path"])
        for artifact in run_report.get("inputs") or []
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    ]
    if actual_inputs != expected_inputs:
        failures.append("run report inputs do not match readiness analysis inputs")

    expected_summary = _command_json_output(command)
    summary_json = run_report.get("summary_json")
    if isinstance(expected_summary, str) and isinstance(summary_json, str):
        if _resolved_artifact_identity(root_path, summary_json) != _resolved_artifact_identity(
            root_path,
            expected_summary,
        ):
            failures.append("run report summary_json does not match readiness analyzer output")
    elif expected_summary or summary_json:
        failures.append("run report summary_json does not match readiness analyzer output")
    return failures


def _fixture_promotion_failures(
    root_path: Path,
    gate_id: str,
    run_report: dict[str, Any] | None,
) -> list[str]:
    if not run_report:
        return ["fixture runner report is missing"]
    if run_report.get("status") == "missing" and run_report.get("path") is None:
        return ["fixture runner report is missing"]
    failures = run_report.get("failures") or []
    promotion_failures: list[str] = []
    if run_report.get("schema") != FIXTURE_RUN_REPORT_SCHEMA:
        promotion_failures.append(
            f"run report schema is {run_report.get('schema')!r}"
        )
    if not isinstance(run_report.get("generated_at"), str) or not run_report.get("generated_at"):
        promotion_failures.append("run report generated_at is missing")
    if not isinstance(run_report.get("root"), str) or not run_report.get("root"):
        promotion_failures.append("run report root is missing")
    if run_report.get("status") != "passed":
        promotion_failures.append(f"run report status is {run_report.get('status')!r}")
    if run_report.get("pass") is not True:
        promotion_failures.append("run report pass is not true")
    if run_report.get("gate") != gate_id:
        promotion_failures.append(f"run report gate is {run_report.get('gate')!r}")
    if failures != []:
        promotion_failures.append("run report failures are not empty")
    promotion_failures.extend(
        _readiness_promotion_failures(root_path, gate_id, run_report)
    )

    inputs = run_report.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        promotion_failures.append("run report inputs are missing")
    else:
        for index, artifact in enumerate(inputs):
            prefix = f"run report inputs[{index}]"
            if not isinstance(artifact, dict):
                promotion_failures.append(f"{prefix} is not an artifact object")
                continue
            if artifact.get("exists") is not True:
                promotion_failures.append(f"{prefix} does not exist")
            if not isinstance(artifact.get("path"), str) or not artifact.get("path"):
                promotion_failures.append(f"{prefix}.path is missing")
            if not isinstance(artifact.get("bytes"), int) or artifact.get("bytes") <= 0:
                promotion_failures.append(f"{prefix}.bytes is missing")
            sha256 = artifact.get("sha256")
            if not isinstance(sha256, str) or len(sha256) != 64:
                promotion_failures.append(f"{prefix}.sha256 is missing")
            promotion_failures.extend(
                _artifact_integrity_failures(root_path, prefix, artifact)
            )

    summary_json = run_report.get("summary_json")
    if not isinstance(summary_json, str) or not summary_json:
        promotion_failures.append("run report summary_json is missing")
        return promotion_failures

    summary_artifact = run_report.get("summary_artifact")
    if not isinstance(summary_artifact, dict):
        promotion_failures.append("run report summary_artifact is missing")
    else:
        if summary_artifact.get("exists") is not True:
            promotion_failures.append("run report summary_artifact does not exist")
        if summary_artifact.get("path") != summary_json:
            promotion_failures.append("run report summary_artifact path does not match summary_json")
        if not isinstance(summary_artifact.get("bytes"), int) or summary_artifact.get("bytes") <= 0:
            promotion_failures.append("run report summary_artifact.bytes is missing")
        sha256 = summary_artifact.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            promotion_failures.append("run report summary_artifact.sha256 is missing")
        promotion_failures.extend(
            _artifact_integrity_failures(
                root_path,
                "run report summary_artifact",
                summary_artifact,
            )
        )

    summary_path = _resolve_artifact_path(root_path, summary_json)
    if not summary_path.exists():
        promotion_failures.append(f"summary JSON missing: {summary_json}")
        return promotion_failures

    summary = _load_json(summary_path)
    if summary is None:
        promotion_failures.append(f"summary JSON invalid: {summary_json}")
    elif not _json_passes(summary):
        promotion_failures.append(f"summary JSON did not report pass:true: {summary_json}")
    return promotion_failures


def audit(
    root: str | Path = DEFAULT_FG23_ROOT,
    *,
    rollup_doc: str = DEFAULT_ROLLUP_DOC,
) -> dict[str, Any]:
    root_path = Path(root)
    rollup_path = root_path / rollup_doc
    rollup_text = _read_text(rollup_path)
    gate_results: list[dict[str, Any]] = []
    for gate in GATES:
        readiness = (
            _latest_readiness(root_path, gate.gate_id)
            if gate.target_status in {"partial", "blocked"}
            else None
        )
        run_report = (
            _latest_run_report(root_path, gate.gate_id)
            if gate.target_status in {"partial", "blocked"}
            else None
        )
        evidence_results = []
        missing = []
        weak = []
        missing_rollup_refs = []
        missing_rollup_blockers = []
        for item in gate.evidence:
            path = root_path / item.path
            exists = path.exists()
            result: dict[str, Any] = {
                "path": item.path,
                "kind": item.kind,
                "exists": exists,
            }
            if item.validator:
                result["validator"] = item.validator
            if not exists:
                missing.append(item.path)
            elif item.kind == "json":
                data = _load_json(path)
                result["json_valid"] = data is not None
                if data is None:
                    weak.append(f"{item.path}: invalid JSON")
                elif item.expect_pass:
                    validation_failures = _json_validation_failures(data, item.validator)
                    result["pass"] = not validation_failures
                    if validation_failures:
                        weak.extend(
                            f"{item.path}: {failure}"
                            for failure in validation_failures
                        )
            if exists and item.kind == "doc" and item.path.endswith(".md"):
                reference_name = _rollup_reference_name(item.path)
                result["rollup_referenced"] = (
                    rollup_text is not None and reference_name in rollup_text
                )
                if not result["rollup_referenced"]:
                    missing_rollup_refs.append(reference_name)
            evidence_results.append(result)
        missing_rollup_blockers = [
            blocker
            for blocker in gate.blockers
            if not _blocker_represented(blocker, rollup_text)
        ]
        fixture_promotion_failures = (
            _fixture_promotion_failures(root_path, gate.gate_id, run_report)
            if gate.target_status in {"partial", "blocked"}
            else []
        )

        if missing:
            actual_status = "missing-evidence"
        elif rollup_text is None:
            weak.append(f"{rollup_doc}: missing rollup document")
            actual_status = "weak-evidence"
        elif weak:
            actual_status = "weak-evidence"
        elif missing_rollup_refs:
            weak.extend(
                f"{rollup_doc}: missing reference to {name}"
                for name in missing_rollup_refs
            )
            actual_status = "weak-evidence"
        elif gate.target_status in {"partial", "blocked"} and not fixture_promotion_failures:
            actual_status = "passed"
        elif missing_rollup_blockers:
            weak.extend(
                f"{rollup_doc}: missing blocker coverage for {blocker}"
                for blocker in missing_rollup_blockers
            )
            actual_status = "weak-evidence"
        else:
            actual_status = gate.target_status
        promoted_by_fixture = actual_status == "passed" and gate.target_status in {
            "partial",
            "blocked",
        }

        gate_results.append(
            {
                "gate": gate.gate_id,
                "name": gate.name,
                "target_status": gate.target_status,
                "status": actual_status,
                "evidence": evidence_results,
                "missing": missing,
                "weak": weak,
                "missing_rollup_refs": missing_rollup_refs,
                "missing_rollup_blockers": missing_rollup_blockers,
                "fixture_promotion_failures": fixture_promotion_failures,
                "blockers": [] if promoted_by_fixture else list(gate.blockers),
                "next_actions": (
                    []
                    if promoted_by_fixture
                    else list(concrete_next_actions(gate.gate_id) or gate.next_actions)
                ),
                "fixture_evidence_promoted": promoted_by_fixture,
                "readiness": readiness,
                "run_report": run_report,
            }
        )

    passed = [gate for gate in gate_results if gate["status"] == "passed"]
    partial = [gate for gate in gate_results if gate["status"] == "partial"]
    blocked = [gate for gate in gate_results if gate["status"] == "blocked"]
    problem = [
        gate
        for gate in gate_results
        if gate["status"] in {"missing-evidence", "weak-evidence"}
    ]
    return {
        "root": str(root_path),
        "rollup_doc": rollup_doc,
        "summary": {
            "passed": len(passed),
            "partial": len(partial),
            "blocked": len(blocked),
            "problem": len(problem),
            "total": len(gate_results),
        },
        "gates": gate_results,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Prototype 0 Gate Audit",
        "",
        f"Root: `{report['root']}`",
        "",
        "| Gate | Status | Evidence | Readiness | Run Report | Blockers | Next Actions |",
        "|---|---|---:|---|---|---|---|",
    ]
    for gate in report["gates"]:
        evidence_count = sum(1 for item in gate["evidence"] if item["exists"])
        readiness = gate.get("readiness")
        readiness_text = ""
        if readiness:
            readiness_text = readiness["status"]
            if readiness.get("path"):
                readiness_text += f"<br>`{readiness['path']}`"
            if readiness.get("failures"):
                readiness_text += "<br>" + "<br>".join(readiness["failures"][:3])
            artifacts = readiness.get("analysis_artifacts")
            if artifacts:
                readiness_text += (
                    f"<br>analysis inputs: {artifacts['inputs_present']}/"
                    f"{artifacts['inputs_total']}"
                )
                summary = artifacts.get("summary")
                if summary:
                    if summary["exists"]:
                        state = "pass" if summary.get("pass") else "not-pass"
                    else:
                        state = "missing"
                    readiness_text += f"<br>summary: {state}"
        blockers = "<br>".join(gate["blockers"]) if gate["blockers"] else ""
        run_report = gate.get("run_report")
        run_report_text = ""
        if run_report:
            run_report_text = run_report["status"]
            if run_report.get("path"):
                run_report_text += f"<br>`{run_report['path']}`"
            if run_report.get("failures"):
                run_report_text += "<br>" + "<br>".join(run_report["failures"][:2])
        next_actions = "<br>".join(f"`{action}`" for action in gate["next_actions"])
        lines.append(
            f"| {gate['gate']} {gate['name']} | {gate['status']} | "
            f"{evidence_count}/{len(gate['evidence'])} | {readiness_text} | "
            f"{run_report_text} | {blockers} | {next_actions} |"
        )
    lines.append("")
    summary = report["summary"]
    lines.append(
        f"Summary: {summary['passed']} passed, {summary['partial']} partial, "
        f"{summary['blocked']} blocked, {summary['problem']} evidence problems."
    )
    return "\n".join(lines) + "\n"


def render_mermaid(report: dict[str, Any]) -> str:
    status_class = {
        "passed": "passed",
        "partial": "partial",
        "blocked": "blocked",
        "missing-evidence": "problem",
        "weak-evidence": "problem",
    }
    lines = [
        "flowchart LR",
        '  classDef passed fill:#d1fae5,stroke:#047857,color:#064e3b',
        '  classDef partial fill:#fef3c7,stroke:#b45309,color:#78350f',
        '  classDef blocked fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d',
        '  classDef problem fill:#f3e8ff,stroke:#7e22ce,color:#581c87',
    ]
    previous_node = None
    for index, gate in enumerate(report["gates"], start=1):
        node = gate["gate"].replace("-", "")
        readiness = gate.get("readiness")
        readiness_line = f"\\nreadiness: {readiness['status']}" if readiness else ""
        run_report = gate.get("run_report")
        run_report_line = f"\\nrun: {run_report['status']}" if run_report else ""
        label = (
            f"{gate['gate']}\\n{gate['name']}\\n"
            f"{gate['status']}\\n"
            f"{sum(1 for item in gate['evidence'] if item['exists'])}/"
            f"{len(gate['evidence'])} evidence"
            f"{readiness_line}"
            f"{run_report_line}"
        )
        lines.append(f'  {node}["{label}"]')
        if previous_node is not None:
            lines.append(f"  {previous_node} --> {node}")
        lines.append(f"  class {node} {status_class.get(gate['status'], 'problem')}")
        previous_node = node
    summary = report["summary"]
    lines.append(
        '  Summary["'
        f"{summary['passed']} passed / {summary['partial']} partial / "
        f"{summary['blocked']} blocked / {summary['problem']} problems"
        '"]'
    )
    if previous_node is not None:
        lines.append(f"  {previous_node} --> Summary")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit OpenRef Prototype 0 gate evidence.")
    parser.add_argument("--root", type=Path, default=DEFAULT_FG23_ROOT)
    parser.add_argument("--rollup-doc", default=DEFAULT_ROLLUP_DOC)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--mermaid", type=Path)
    args = parser.parse_args()

    report = audit(args.root, rollup_doc=args.rollup_doc)
    print(render_markdown(report))
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown is not None:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    if args.mermaid is not None:
        args.mermaid.parent.mkdir(parents=True, exist_ok=True)
        args.mermaid.write_text(render_mermaid(report), encoding="utf-8")

    raise SystemExit(1 if report["summary"]["problem"] else 0)


if __name__ == "__main__":
    main()
