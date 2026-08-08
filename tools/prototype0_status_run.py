from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

from audit_prototype0_gates import audit, render_markdown as render_audit_markdown
from capture_serial import _load_serial
from prototype0_fixture_capture_templates import CAPTURE_TEMPLATES
from prototype0_fixture_actions import (
    check_command as fixture_check_command,
    dry_run_command as fixture_dry_run_command,
    fixture_action_details,
    run_command as fixture_run_command,
    template_command as fixture_template_command,
)
from run_prototype0_fixture_analysis import DISCOVERABLE_GATES, discover_readiness, run


DEFAULT_ROOT = Path("firmware/prototype0/fg23")
DEFAULT_CAPTURE_TEMPLATE_DIR = Path("templates/fixture-captures")
DEFAULT_CAPTURE_TEMPLATE_MANIFEST = "capture-template-manifest.json"
DEFAULT_POWER_PORTS = ("COM8", "COM10")
DEFAULT_PACKET_RX_PORT = "COM8"
DEFAULT_PACKET_TX_PORT = "COM10"
DEFAULT_PACKET_COUNT = 20
DEFAULT_RF_PATH = 0
POWER_TIMEOUT_SECONDS = 1.0
DEFAULT_TEST_ARGS = [
    "-B",
    "-m",
    "pytest",
    "-q",
    "-p",
    "no:cacheprovider",
    "simulator/tests",
    "tools/tests",
    "--basetemp",
    ".pytest-tmp",
]


STATUS_FIELD_RE = re.compile(r"\{(?P<key>[A-Za-z0-9]+):(?P<value>[^}]+)\}")
LOG_PATH_RE = re.compile(r"^(?P<label>RX|TX) log: (?P<path>.+)$", re.MULTILINE)

FIXTURE_BENCH_DETAILS = {
    "E0-03": {
        "instrument": "logic analyzer or oscilloscope",
        "setup": "Ground connected; PB3 queue marker and PB2 TX-start marker; optional PB0 build and PA5 TX-done markers.",
        "capture": "Export edge timestamps to firmware/prototype0/fg23/results/YYYYMMDD-e0-03-scheduled-tx-gpio.csv.",
        "minimum_evidence": "At least 100 paired queue/start samples at 5 MHz or faster.",
        "pass_criteria": "Analyzer summary pass:true with paired samples present, launch-error stats, and no unpaired edges when --fail-on-unpaired-edges is used.",
        "input_template_command": "python tools/prototype0_fixture_capture_templates.py --gate E0-03 --output-dir firmware/prototype0/fg23/templates/fixture-captures",
    },
    "E0-05": {
        "instrument": "controlled RF attenuator, shield box, or repeatable shielding method",
        "setup": "RF path 0; same RX/TX direction for every step; same packet count, payload, and timing for baseline and attenuated runs.",
        "capture": "Write one baseline packet summary JSON and one or more attenuated step summary JSON files.",
        "minimum_evidence": "At least two valid packet-summary steps with physical setup notes and unique step labels.",
        "pass_criteria": "Analyzer summary pass:true with a valid baseline and at least one attenuated step reaching the configured packet-error threshold.",
        "input_template_command": "python tools/prototype0_fixture_capture_templates.py --gate E0-05 --output-dir firmware/prototype0/fg23/templates/fixture-captures",
    },
    "E0-07": {
        "instrument": "audio capture/playback fixture plus firmware timing markers",
        "setup": "Capture impulse, capture_frame, packet_queue, tx_start, rx_done, and playback_output events for each frame.",
        "capture": "Export event timing rows to firmware/prototype0/fg23/results/YYYYMMDD-e0-07-audio-loopback.csv.",
        "minimum_evidence": "At least 10 complete impulse-to-playback event chains.",
        "pass_criteria": "Analyzer summary pass:true with p95 end-to-end latency at or below 120 ms and max at or below 180 ms.",
        "input_template_command": "python tools/prototype0_fixture_capture_templates.py --gate E0-07 --output-dir firmware/prototype0/fg23/templates/fixture-captures",
    },
}

FIXTURE_NON_CLOSURE_GUARDRAILS = (
    {
        "gate": "E0-03",
        "accepted_closure_evidence": (
            "A v1 fixture run report passing from external GPIO/logic-analyzer or oscilloscope "
            "capture of scheduled-TX queue/start markers."
        ),
        "non_closing_prechecks": (
            "RAILtest scheduled-TX API-path success",
            "OpenRef SDK timestamp launch-error summary",
            "GPIO marker pin/build plan without the exported capture CSV",
        ),
    },
    {
        "gate": "E0-05",
        "accepted_closure_evidence": (
            "A v1 fixture run report passing from same-direction baseline plus controlled "
            "attenuated or repeatably shielded packet-summary steps."
        ),
        "non_closing_prechecks": (
            "same-bench RF path 0 baseline packet delivery by itself",
            "software TX-power reduction/link-margin sweep",
            "RSSI tone health check on RF path 0",
            "RF path 1 expected-negative/no-tone behavior",
        ),
    },
    {
        "gate": "E0-07",
        "accepted_closure_evidence": (
            "A v1 fixture run report passing from audio loopback timing capture with impulse, "
            "capture, queue, TX, RX, and playback markers."
        ),
        "non_closing_prechecks": (
            "audio-loopback analysis plan without capture",
            "capture-template CSV shape examples",
            "firmware marker intent without exported event timing rows",
        ),
    },
)


def parse_power_deci_dbm(output: str) -> int | None:
    marker = "{power:"
    start = output.find(marker)
    if start < 0:
        return None
    start += len(marker)
    end = output.find("}", start)
    if end < 0:
        return None
    try:
        return int(output[start:end])
    except ValueError:
        return None


def _query_power(port: str, *, baud: int = 115200) -> dict[str, Any]:
    try:
        serial, _ = _load_serial()
        with serial.Serial(port, baudrate=baud, timeout=POWER_TIMEOUT_SECONDS) as handle:
            if hasattr(handle, "reset_input_buffer"):
                handle.reset_input_buffer()
            handle.write(b"getPower\r\n")
            if hasattr(handle, "flush"):
                handle.flush()
            time.sleep(0.35)
            raw = handle.read(4096)
        output = raw.decode("utf-8", errors="replace")
        deci_dbm = parse_power_deci_dbm(output)
        return {
            "port": port,
            "pass": deci_dbm is not None,
            "power_deci_dbm": deci_dbm,
            "power_dbm": deci_dbm / 10 if deci_dbm is not None else None,
            "raw": output,
            "failures": [] if deci_dbm is not None else ["getPower response did not include power"],
        }
    except BaseException as exc:
        return {
            "port": port,
            "pass": False,
            "power_deci_dbm": None,
            "power_dbm": None,
            "raw": "",
            "failures": [str(exc)],
        }


def _add_power_response_fingerprint(board: dict[str, Any]) -> dict[str, Any]:
    raw = board.get("raw")
    if not isinstance(raw, str):
        raw = ""
    encoded = raw.encode("utf-8", errors="replace")
    enriched = dict(board)
    enriched["raw_bytes"] = len(encoded)
    enriched["raw_sha256"] = hashlib.sha256(encoded).hexdigest()
    return enriched


def _power_check(ports: tuple[str, ...] | list[str]) -> dict[str, Any]:
    boards = [
        _add_power_response_fingerprint(_query_power(port))
        for port in ports
    ]
    return {
        "pass": all(item["pass"] for item in boards),
        "ports": list(ports),
        "boards": boards,
    }


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


def _last_status_fields(text: str) -> dict[str, str]:
    statuses = [line for line in text.splitlines() if "{{(status)}" in line]
    if not statuses:
        return {}
    return {
        match.group("key"): match.group("value")
        for match in STATUS_FIELD_RE.finditer(statuses[-1])
    }


def parse_packet_smoke_stdout(stdout: str) -> dict[str, str]:
    return {
        match.group("label").lower() + "_log": match.group("path").strip()
        for match in LOG_PATH_RE.finditer(stdout)
    }


def _file_artifact(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "exists": False,
            "bytes": None,
            "sha256": None,
            "mtime_utc": None,
        }
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


def summarize_packet_smoke_logs(rx_log: Path | None, tx_log: Path | None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "rx_log": str(rx_log) if rx_log is not None else None,
        "tx_log": str(tx_log) if tx_log is not None else None,
        "rx_log_exists": rx_log.exists() if rx_log is not None else False,
        "tx_log_exists": tx_log.exists() if tx_log is not None else False,
        "rx_log_artifact": _file_artifact(rx_log),
        "tx_log_artifact": _file_artifact(tx_log),
        "rx_packet_lines": None,
        "rx_count": None,
        "rx_crc_err_drop": None,
        "rx_overflow": None,
        "tx_transmitted": None,
        "tx_user_tx_started": None,
    }
    if rx_log is not None and rx_log.exists():
        rx_text = rx_log.read_text(encoding="utf-8", errors="replace")
        rx_fields = _last_status_fields(rx_text)
        summary["rx_packet_lines"] = rx_text.count("{{(rxPacket)}")
        summary["rx_count"] = _parse_int(rx_fields.get("RxCount"))
        summary["rx_crc_err_drop"] = _parse_int(rx_fields.get("RxCrcErrDrop"))
        summary["rx_overflow"] = _parse_int(rx_fields.get("RxOverflow"))
    if tx_log is not None and tx_log.exists():
        tx_text = tx_log.read_text(encoding="utf-8", errors="replace")
        tx_fields = _last_status_fields(tx_text)
        tx_end = [line for line in tx_text.splitlines() if "{{(txEnd)}" in line]
        if tx_end:
            tx_end_fields = {
                match.group("key"): match.group("value")
                for match in STATUS_FIELD_RE.finditer(tx_end[-1])
            }
            summary["tx_transmitted"] = _parse_int(tx_end_fields.get("transmitted"))
        summary["tx_user_tx_started"] = _parse_int(tx_fields.get("UserTxStarted"))
    return summary


def validate_packet_smoke_evidence(evidence: dict[str, Any], expected_packets: int) -> list[str]:
    failures = []
    if not evidence.get("rx_log_exists"):
        failures.append("RX log missing")
    if not evidence.get("tx_log_exists"):
        failures.append("TX log missing")
    expected_values = {
        "rx_packet_lines": expected_packets,
        "rx_count": expected_packets,
        "tx_transmitted": expected_packets,
        "tx_user_tx_started": expected_packets,
    }
    for key, expected in expected_values.items():
        if evidence.get(key) != expected:
            failures.append(f"{key} expected {expected}, got {evidence.get(key)}")
    zero_values = ("rx_crc_err_drop", "rx_overflow")
    for key in zero_values:
        if evidence.get(key) != 0:
            failures.append(f"{key} expected 0, got {evidence.get(key)}")
    return failures


def _audit_gate_by_id(audit_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        gate["gate"]: gate
        for gate in audit_report.get("gates", [])
        if isinstance(gate, dict) and isinstance(gate.get("gate"), str)
    }


def _fixture_dry_runs(
    root: Path,
    audit_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    audit_gates = _audit_gate_by_id(audit_report or {})
    results = []
    for gate in sorted(DISCOVERABLE_GATES):
        readiness = discover_readiness(root, gate)
        if readiness is None:
            audit_readiness = (audit_gates.get(gate) or {}).get("readiness") or {}
            failures = [f"no live readiness file found under {root / 'results'}"]
            if audit_readiness.get("path"):
                failures.append(
                    f"latest manifest readiness {audit_readiness['path']} is "
                    f"{audit_readiness.get('status', 'unknown')}"
                )
            failures.extend(audit_readiness.get("failures") or [])
            results.append(
                {
                    "gate": gate,
                    "status": "no-readiness",
                    "readiness": audit_readiness.get("path"),
                    "audit_readiness_status": audit_readiness.get("status"),
                    "pass": False,
                    "expected_external_input": True,
                    "failures": failures,
                }
            )
            continue
        report = run(readiness, root=root, dry_run=True)
        report["expected_external_input"] = report["status"] in {
            "dry-run",
            "not-ready",
            "missing-inputs",
            "no-readiness",
        }
        results.append(report)
    return results


def external_actions(audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    actions = []
    for gate in audit_report["gates"]:
        if gate["status"] not in {"partial", "blocked"}:
            continue
        readiness = gate.get("readiness") or {}
        run_report = gate.get("run_report") or {}
        blockers = gate.get("blockers", [])
        promotion_failures = gate.get("fixture_promotion_failures") or []
        action_details = fixture_action_details(gate["gate"])
        filled_readiness = action_details.get("filled_readiness")
        if readiness.get("status") == "ready" and filled_readiness:
            next_command = fixture_run_command(gate["gate"]) or fixture_dry_run_command(gate["gate"])
        else:
            next_command = action_details.get("fill_command") or (gate.get("next_actions", []) or [""])[0]
        actions.append(
            {
                "gate": gate["gate"],
                "name": gate["name"],
                "status": gate["status"],
                "blockers": blockers,
                "external_blocker": bool(blockers),
                "blocker_type": "external-fixture" if blockers else None,
                "readiness_status": readiness.get("status"),
                "readiness_path": readiness.get("path"),
                "run_report_status": run_report.get("status"),
                "run_report_path": run_report.get("path"),
                "fixture_evidence_promoted": gate.get("fixture_evidence_promoted"),
                "fixture_promotion_failures": promotion_failures,
                "next_actions": gate.get("next_actions", []),
                "next_command": next_command,
            }
        )
    return actions


def fixture_action_plan(audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    plan = []
    for gate in audit_report["gates"]:
        if gate["status"] not in {"partial", "blocked"}:
            continue
        readiness = gate.get("readiness") or {}
        run_report = gate.get("run_report") or {}
        actions = gate.get("next_actions", [])
        blockers = gate.get("blockers") or []
        promotion_failures = gate.get("fixture_promotion_failures") or []
        details = FIXTURE_BENCH_DETAILS.get(gate["gate"], {})
        action_details = fixture_action_details(gate["gate"])
        template_command = fixture_template_command(gate["gate"]) or (
            actions[0] if len(actions) > 0 else None
        )
        check_command = fixture_check_command(gate["gate"]) or (
            actions[1] if len(actions) > 1 else None
        )
        fill_command = action_details.get("fill_command")
        dry_run_command = fixture_dry_run_command(gate["gate"]) or (
            actions[2] if len(actions) > 2 else None
        )
        run_command = fixture_run_command(gate["gate"]) or (
            actions[3] if len(actions) > 3 else None
        )
        discover_dry_run_command = next(
            (
                action
                for action in actions
                if f"--gate {gate['gate']} --dry-run" in action
            ),
            None,
        )
        discover_run_command = next(
            (
                action
                for action in actions
                if f"--gate {gate['gate']} --json" in action
            ),
            None,
        )
        plan.append(
            {
                "gate": gate["gate"],
                "name": gate["name"],
                "status": gate["status"],
                "external_input": "; ".join(blockers),
                "external_blocker": bool(blockers),
                "blocker_type": "external-fixture" if blockers else None,
                "readiness_status": readiness.get("status"),
                "readiness_path": readiness.get("path"),
                "run_report_status": run_report.get("status"),
                "run_report_path": run_report.get("path"),
                "fixture_evidence_promoted": gate.get("fixture_evidence_promoted"),
                "fixture_promotion_failures": promotion_failures,
                "template_command": template_command,
                "check_command": check_command,
                "fill_command": fill_command,
                "dry_run_command": dry_run_command,
                "run_command": run_command,
                "discover_dry_run_command": discover_dry_run_command,
                "discover_run_command": discover_run_command,
            }
        )
    return plan


def fixture_bench_checklist(action_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checklist = []
    for item in action_plan:
        details = FIXTURE_BENCH_DETAILS.get(item["gate"], {})
        checklist.append(
            {
                "gate": item["gate"],
                "name": item["name"],
                "status": item["status"],
                "external_input": item.get("external_input"),
                "external_blocker": item.get("external_blocker"),
                "blocker_type": item.get("blocker_type"),
                "instrument": details.get("instrument"),
                "setup": details.get("setup"),
                "capture": details.get("capture"),
                "minimum_evidence": details.get("minimum_evidence"),
                "pass_criteria": details.get("pass_criteria"),
                "input_template_command": details.get("input_template_command"),
                "prepare_command": item.get("template_command"),
                "fill_command": item.get("fill_command"),
                "verify_command": item.get("dry_run_command"),
                "execute_command": item.get("run_command"),
            }
        )
    return checklist


def fixture_capture_template_status(root: Path) -> dict[str, Any]:
    template_dir = root / DEFAULT_CAPTURE_TEMPLATE_DIR
    manifest_path = template_dir / DEFAULT_CAPTURE_TEMPLATE_MANIFEST
    manifest = None
    manifest_valid = False
    manifest_pass = False
    manifest_failures: list[str] = []
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_valid = isinstance(manifest, dict)
        except json.JSONDecodeError as exc:
            manifest_failures.append(f"manifest JSON invalid: {exc}")
    else:
        manifest_failures.append("manifest missing")

    if manifest_valid:
        manifest_pass = manifest.get("pass") is True
        if not manifest_pass:
            manifest_failures.append("manifest pass is not true")
        if manifest.get("gate") != "all":
            manifest_failures.append(f"manifest gate is {manifest.get('gate')!r}")
        templates = manifest.get("templates")
        if not isinstance(templates, list) or len(templates) != sum(
            len(entries) for entries in CAPTURE_TEMPLATES.values()
        ):
            manifest_failures.append("manifest template count does not match expected templates")

    files = []
    for gate, entries in CAPTURE_TEMPLATES.items():
        for filename, expected_content in entries:
            path = template_dir / filename
            exists = path.exists()
            content_matches = (
                path.read_text(encoding="utf-8") == expected_content
                if exists
                else False
            )
            files.append(
                {
                    "gate": gate,
                    "path": str(path),
                    "exists": exists,
                    "content_matches": content_matches,
                    "bytes": len(path.read_bytes()) if exists else None,
                    "expected_bytes": len(expected_content.encode("utf-8")),
                }
            )

    file_failures = [
        f"{item['path']}: {'missing' if not item['exists'] else 'content mismatch'}"
        for item in files
        if not item["exists"] or not item["content_matches"]
    ]
    return {
        "pass": manifest_valid and manifest_pass and not manifest_failures and not file_failures,
        "template_dir": str(template_dir),
        "manifest": str(manifest_path),
        "manifest_exists": manifest_path.exists(),
        "manifest_valid": manifest_valid,
        "manifest_pass": manifest_pass,
        "files": files,
        "failures": manifest_failures + file_failures,
        "note": "Capture templates are shape examples only and are not passing fixture evidence.",
    }


def fixture_input_inventory(fixture_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory = []
    for report in fixture_reports:
        inputs = [
            {
                "path": item.get("path"),
                "exists": item.get("exists") is True,
                "bytes": item.get("bytes"),
                "sha256": item.get("sha256"),
                "mtime_utc": item.get("mtime_utc"),
            }
            for item in report.get("inputs") or []
            if isinstance(item, dict)
        ]
        missing = [item["path"] for item in inputs if not item["exists"]]
        present = [item["path"] for item in inputs if item["exists"]]
        inventory.append(
            {
                "gate": report.get("gate"),
                "status": report.get("status"),
                "readiness": report.get("readiness"),
                "summary_json": report.get("summary_json"),
                "inputs_present": len(present),
                "inputs_total": len(inputs),
                "present_inputs": present,
                "missing_inputs": missing,
                "input_artifacts": inputs,
                "all_inputs_present": bool(inputs) and not missing,
                "expected_external_input": report.get("expected_external_input") is True,
            }
        )
    return inventory


def fixture_non_closure_guardrails() -> list[dict[str, Any]]:
    return [
        {
            "gate": item["gate"],
            "accepted_closure_evidence": item["accepted_closure_evidence"],
            "non_closing_prechecks": list(item["non_closing_prechecks"]),
        }
        for item in FIXTURE_NON_CLOSURE_GUARDRAILS
    ]


def external_blocker_summary(
    audit_report: dict[str, Any],
    actions: list[dict[str, Any]],
    inventory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    incomplete_gates = [
        gate["gate"]
        for gate in audit_report.get("gates", [])
        if gate.get("status") in {"partial", "blocked"}
    ]
    external_gates = [
        item["gate"]
        for item in actions
        if item.get("external_blocker") is True
        and item.get("blocker_type") == "external-fixture"
    ]
    unclassified = [
        gate
        for gate in incomplete_gates
        if gate not in set(external_gates)
    ]
    problem_count = int((audit_report.get("summary") or {}).get("problem", 0))
    inventory = inventory or []
    missing_inputs_by_gate = {
        str(item.get("gate")): list(item.get("missing_inputs") or [])
        for item in inventory
        if item.get("gate") in external_gates
    }
    present_inputs_by_gate = {
        str(item.get("gate")): list(item.get("present_inputs") or [])
        for item in inventory
        if item.get("gate") in external_gates
    }
    present_artifacts_by_gate = {
        str(item.get("gate")): [
            artifact
            for artifact in item.get("input_artifacts") or []
            if isinstance(artifact, dict) and artifact.get("exists") is True
        ]
        for item in inventory
        if item.get("gate") in external_gates
    }
    summary_outputs_by_gate = {
        str(item.get("gate")): item.get("summary_json")
        for item in inventory
        if item.get("gate") in external_gates
    }
    all_missing_inputs = [
        path
        for gate in external_gates
        for path in missing_inputs_by_gate.get(gate, [])
    ]
    return {
        "only_external_blockers": problem_count == 0 and not unclassified,
        "incomplete_gates": incomplete_gates,
        "external_blocked_gates": external_gates,
        "unclassified_incomplete_gates": unclassified,
        "evidence_problem_count": problem_count,
        "missing_input_count": len(all_missing_inputs),
        "all_missing_inputs": all_missing_inputs,
        "missing_inputs_by_gate": missing_inputs_by_gate,
        "present_inputs_by_gate": present_inputs_by_gate,
        "present_artifacts_by_gate": present_artifacts_by_gate,
        "summary_outputs_by_gate": summary_outputs_by_gate,
    }


def completion_audit(
    audit_report: dict[str, Any],
    blocker_summary: dict[str, Any],
) -> dict[str, Any]:
    external_gates = set(blocker_summary.get("external_blocked_gates") or [])
    gate_results = []
    for gate in audit_report.get("gates", []):
        gate_id = gate["gate"]
        evidence_total = len(gate.get("evidence") or [])
        evidence_present = sum(1 for item in gate.get("evidence") or [] if item.get("exists"))
        status = gate.get("status")
        if status == "passed":
            classification = "proved"
            complete = True
            reason = "all required evidence is present and passing"
        elif gate_id in external_gates:
            classification = "external"
            complete = False
            promotion_failures = gate.get("fixture_promotion_failures") or []
            suffix = (
                f": {promotion_failures[0]}"
                if promotion_failures
                else ""
            )
            reason = "remaining work requires external fixture evidence" + suffix
        else:
            classification = "not-proved"
            complete = False
            reason = "gate is incomplete without an external-fixture classification"
        gate_results.append(
            {
                "gate": gate_id,
                "name": gate.get("name"),
                "status": status,
                "classification": classification,
                "complete": complete,
                "evidence_present": evidence_present,
                "evidence_total": evidence_total,
                "reason": reason,
                "blockers": gate.get("blockers", []),
                "fixture_evidence_promoted": gate.get("fixture_evidence_promoted"),
                "fixture_promotion_failures": gate.get("fixture_promotion_failures") or [],
            }
        )

    proved = [gate for gate in gate_results if gate["classification"] == "proved"]
    external = [gate for gate in gate_results if gate["classification"] == "external"]
    not_proved = [gate for gate in gate_results if gate["classification"] == "not-proved"]
    return {
        "prototype0_complete": not external and not not_proved,
        "all_remaining_work_external": bool(external) and not not_proved,
        "proved_gates": [gate["gate"] for gate in proved],
        "external_gates": [gate["gate"] for gate in external],
        "not_proved_gates": [gate["gate"] for gate in not_proved],
        "summary": {
            "proved": len(proved),
            "external": len(external),
            "not_proved": len(not_proved),
            "total": len(gate_results),
        },
        "gates": gate_results,
    }


def _run_pytest(cwd: Path, extra_args: list[str] | None = None) -> dict[str, Any]:
    command = [sys.executable, *(extra_args or DEFAULT_TEST_ARGS)]
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return {
        "command": command,
        "returncode": completed.returncode,
        "pass": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _packet_smoke(
    *,
    root: Path,
    rx_port: str,
    tx_port: str,
    rf_path: int,
    packets: int,
    output_label: str | None = None,
) -> dict[str, Any]:
    if output_label is None:
        output_dir = root / "results"
    else:
        output_dir = root / "results" / "status-packet-smoke" / output_label
    command = [
        sys.executable,
        "tools/railtest_pair_smoke.py",
        "--rx-port",
        rx_port,
        "--tx-port",
        tx_port,
        "--rf-path",
        str(rf_path),
        "--packets",
        str(packets),
        "--output-dir",
        output_dir.as_posix(),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    log_paths = parse_packet_smoke_stdout(completed.stdout)
    rx_log = Path(log_paths["rx_log"]) if "rx_log" in log_paths else None
    tx_log = Path(log_paths["tx_log"]) if "tx_log" in log_paths else None
    evidence = summarize_packet_smoke_logs(rx_log, tx_log)
    evidence_failures = validate_packet_smoke_evidence(evidence, packets)
    return {
        "command": command,
        "returncode": completed.returncode,
        "pass": completed.returncode == 0 and not evidence_failures,
        "rx_port": rx_port,
        "tx_port": tx_port,
        "rf_path": rf_path,
        "packets": packets,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "evidence": evidence,
        "evidence_failures": evidence_failures,
    }


def _packet_smokes(
    *,
    root: Path,
    rx_port: str,
    tx_port: str,
    rf_path: int,
    packets: int,
    bidirectional: bool,
) -> list[dict[str, Any]]:
    directions = [(rx_port, tx_port)]
    if bidirectional:
        directions.append((tx_port, rx_port))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    reports = []
    for index, (direction_rx, direction_tx) in enumerate(directions, start=1):
        label = f"{timestamp}-{index:02d}-{direction_tx}-to-{direction_rx}"
        reports.append(
            _packet_smoke(
                root=root,
                rx_port=direction_rx,
                tx_port=direction_tx,
                rf_path=rf_path,
                packets=packets,
                output_label=label,
            )
        )
    return reports


def run_status(
    *,
    root: Path = DEFAULT_ROOT,
    run_pytest: bool = False,
    power_check: bool = False,
    power_ports: tuple[str, ...] | list[str] = DEFAULT_POWER_PORTS,
    packet_smoke: bool = False,
    packet_rx_port: str = DEFAULT_PACKET_RX_PORT,
    packet_tx_port: str = DEFAULT_PACKET_TX_PORT,
    packet_rf_path: int = DEFAULT_RF_PATH,
    packet_count: int = DEFAULT_PACKET_COUNT,
    packet_bidirectional: bool = False,
    pytest_args: list[str] | None = None,
) -> dict[str, Any]:
    audit_report = audit(root)
    fixture_reports = _fixture_dry_runs(root, audit_report)
    fixture_inventory = fixture_input_inventory(fixture_reports)
    actions = external_actions(audit_report)
    action_plan = fixture_action_plan(audit_report)
    capture_template_report = fixture_capture_template_status(root)
    pytest_report = _run_pytest(Path.cwd(), pytest_args) if run_pytest else None
    power_report = _power_check(power_ports) if power_check else None
    packet_reports = (
        _packet_smokes(
            root=root,
            rx_port=packet_rx_port,
            tx_port=packet_tx_port,
            rf_path=packet_rf_path,
            packets=packet_count,
            bidirectional=packet_bidirectional,
        )
        if packet_smoke
        else []
    )
    packet_report = packet_reports[0] if packet_reports else None
    has_evidence_problem = audit_report["summary"]["problem"] != 0
    has_pytest_problem = pytest_report is not None and not pytest_report["pass"]
    has_power_problem = power_report is not None and not power_report["pass"]
    has_packet_problem = any(not item["pass"] for item in packet_reports)
    blocker_summary = external_blocker_summary(audit_report, actions, fixture_inventory)
    return {
        "pass": (
            not has_evidence_problem
            and not has_pytest_problem
            and not has_power_problem
            and not has_packet_problem
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "audit": audit_report,
        "external_actions": actions,
        "external_blocker_summary": blocker_summary,
        "completion_audit": completion_audit(audit_report, blocker_summary),
        "fixture_action_plan": action_plan,
        "fixture_bench_checklist": fixture_bench_checklist(action_plan),
        "fixture_capture_templates": capture_template_report,
        "fixture_input_inventory": fixture_inventory,
        "fixture_non_closure_guardrails": fixture_non_closure_guardrails(),
        "fixture_dry_runs": fixture_reports,
        "pytest": pytest_report,
        "power_check": power_report,
        "packet_smoke": packet_report,
        "packet_smokes": packet_reports,
    }


def render_markdown(report: dict[str, Any]) -> str:
    audit_report = report["audit"]
    summary = audit_report["summary"]
    lines = [
        "# Prototype 0 Status Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Overall pass: `{str(report['pass']).lower()}`",
        "",
        "## Gate Summary",
        "",
        (
            f"{summary['passed']} passed, {summary['partial']} partial, "
            f"{summary['blocked']} blocked, {summary['problem']} evidence problems."
        ),
    ]
    blocker_summary = report.get("external_blocker_summary") or {}
    if blocker_summary:
        lines.extend(
            [
                "",
                "## External Blocker Summary",
                "",
                f"Only external blockers remain: `{str(blocker_summary.get('only_external_blockers')).lower()}`",
                "",
                "| Incomplete Gates | External Fixture Gates | Unclassified | Evidence Problems |",
                "|---|---|---|---:|",
                (
                    f"| {', '.join(blocker_summary.get('incomplete_gates') or [])} | "
                    f"{', '.join(blocker_summary.get('external_blocked_gates') or [])} | "
                    f"{', '.join(blocker_summary.get('unclassified_incomplete_gates') or [])} | "
                    f"{blocker_summary.get('evidence_problem_count', '')} |"
                ),
            ]
        )
        missing_inputs = blocker_summary.get("all_missing_inputs") or []
        if missing_inputs:
            lines.extend(
                [
                    "",
                    f"Missing external input files: `{blocker_summary.get('missing_input_count')}`",
                    "",
                    "| Gate | Missing Inputs | Expected Summary Output |",
                    "|---|---|---|",
                ]
            )
            missing_by_gate = blocker_summary.get("missing_inputs_by_gate") or {}
            summary_by_gate = blocker_summary.get("summary_outputs_by_gate") or {}
            for gate in blocker_summary.get("external_blocked_gates") or []:
                gate_missing = "<br>".join(
                    f"`{path}`" for path in missing_by_gate.get(gate, [])
                )
                summary_output = summary_by_gate.get(gate) or ""
                lines.append(f"| {gate} | {gate_missing} | `{summary_output}` |")
    completion = report.get("completion_audit") or {}
    if completion:
        completion_summary = completion.get("summary") or {}
        lines.extend(
            [
                "",
                "## Completion Audit",
                "",
                f"Prototype 0 complete: `{str(completion.get('prototype0_complete')).lower()}`",
                f"All remaining work external: `{str(completion.get('all_remaining_work_external')).lower()}`",
                "",
                "| Classification | Gates | Count |",
                "|---|---|---:|",
                f"| proved | {', '.join(completion.get('proved_gates') or [])} | {completion_summary.get('proved', '')} |",
                f"| external | {', '.join(completion.get('external_gates') or [])} | {completion_summary.get('external', '')} |",
                f"| not-proved | {', '.join(completion.get('not_proved_gates') or [])} | {completion_summary.get('not_proved', '')} |",
            ]
        )
    lines.extend(
        [
            "",
            "## Fixture Dry Runs",
            "",
            "| Gate | Status | Readiness | Inputs | Notes |",
            "|---|---|---|---:|---|",
        ]
    )
    for item in report["fixture_dry_runs"]:
        inputs = item.get("inputs", [])
        present = sum(1 for entry in inputs if entry.get("exists"))
        readiness = item.get("readiness") or ""
        failures = item.get("failures") or []
        lines.append(
            f"| {item['gate']} | {item['status']} | `{readiness}` | "
            f"{present}/{len(inputs)} | {'<br>'.join(failures[:2])} |"
        )
    readiness_artifacts = [
        (item.get("gate"), artifact)
        for item in report["fixture_dry_runs"]
        for artifact in [item.get("readiness_artifact")]
        if isinstance(artifact, dict) and artifact.get("exists") is True
    ]
    if readiness_artifacts:
        lines.extend(
            [
                "",
                "## Fixture Readiness Provenance",
                "",
                "| Gate | Readiness | Bytes | SHA-256 | Modified UTC |",
                "|---|---|---:|---|---|",
            ]
        )
        for gate, artifact in readiness_artifacts:
            lines.append(
                f"| {gate} | `{artifact.get('path') or ''}` | "
                f"{artifact.get('bytes') or ''} | `{artifact.get('sha256') or ''}` | "
                f"{artifact.get('mtime_utc') or ''} |"
            )
    inventory = report.get("fixture_input_inventory") or []
    if inventory:
        lines.extend(
            [
                "",
                "## Fixture Input Inventory",
                "",
                "| Gate | Inputs | Present | Missing | Summary Output |",
                "|---|---:|---|---|---|",
            ]
        )
        for item in inventory:
            present_inputs = "<br>".join(f"`{path}`" for path in item.get("present_inputs") or [])
            missing_inputs = "<br>".join(f"`{path}`" for path in item.get("missing_inputs") or [])
            summary_json = item.get("summary_json") or ""
            lines.append(
                f"| {item.get('gate')} | {item.get('inputs_present')}/{item.get('inputs_total')} | "
                f"{present_inputs} | {missing_inputs} | `{summary_json}` |"
            )
        present_artifacts = [
            (item.get("gate"), artifact)
            for item in inventory
            for artifact in item.get("input_artifacts") or []
            if isinstance(artifact, dict) and artifact.get("exists") is True
        ]
        if present_artifacts:
            lines.extend(
                [
                    "",
                    "## Fixture Artifact Provenance",
                    "",
                    "| Gate | Input | Bytes | SHA-256 | Modified UTC |",
                    "|---|---|---:|---|---|",
                ]
            )
            for gate, artifact in present_artifacts:
                lines.append(
                    f"| {gate} | `{artifact.get('path') or ''}` | "
                    f"{artifact.get('bytes') or ''} | `{artifact.get('sha256') or ''}` | "
                    f"{artifact.get('mtime_utc') or ''} |"
                )
    guardrails = report.get("fixture_non_closure_guardrails") or []
    if guardrails:
        lines.extend(
            [
                "",
                "## Fixture Non-Closure Guardrails",
                "",
                "| Gate | Accepted Closure Evidence | Non-Closing Prechecks |",
                "|---|---|---|",
            ]
        )
        for item in guardrails:
            non_closing = "<br>".join(item.get("non_closing_prechecks") or [])
            lines.append(
                f"| {item.get('gate')} | {item.get('accepted_closure_evidence') or ''} | "
                f"{non_closing} |"
            )
    external = report.get("external_actions") or []
    if external:
        lines.extend(
            [
                "",
                "## External Actions",
                "",
                "| Gate | Status | Readiness | Run Report | Promotion | Blocker | Next Command |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for item in external:
            blocker = "<br>".join(item.get("blockers") or [])
            promotion = "<br>".join(item.get("fixture_promotion_failures") or [])
            next_command = item.get("next_command") or (item.get("next_actions") or [""])[0]
            readiness = item.get("readiness_status") or ""
            run_report = item.get("run_report_status") or ""
            lines.append(
                f"| {item['gate']} {item['name']} | {item['status']} | "
                f"{readiness} | {run_report} | {promotion} | {blocker} | `{next_command}` |"
            )
    action_plan = report.get("fixture_action_plan") or []
    if action_plan:
        lines.extend(
            [
                "",
                "## Fixture Action Plan",
                "",
                "| Gate | External Input | Prepare | Fill | Verify | Execute |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in action_plan:
            external_input = item.get("external_input") or ""
            prepare = item.get("template_command") or ""
            fill = item.get("fill_command") or ""
            verify = item.get("dry_run_command") or ""
            execute = item.get("run_command") or ""
            lines.append(
                f"| {item['gate']} {item['name']} | {external_input} | "
                f"`{prepare}` | `{fill}` | `{verify}` | `{execute}` |"
            )
    capture_templates = report.get("fixture_capture_templates") or {}
    if capture_templates:
        lines.extend(
            [
                "",
                "## Fixture Capture Templates",
                "",
                f"Pass: `{str(capture_templates.get('pass')).lower()}`",
                "",
                f"Directory: `{capture_templates.get('template_dir')}`",
                "",
                f"Manifest: `{capture_templates.get('manifest')}`",
                "",
                f"Note: {capture_templates.get('note')}",
                "",
                "| Gate | Template | Exists | Content Matches |",
                "|---|---|---:|---:|",
            ]
        )
        for item in capture_templates.get("files") or []:
            lines.append(
                f"| {item.get('gate')} | `{item.get('path')}` | "
                f"{str(item.get('exists')).lower()} | {str(item.get('content_matches')).lower()} |"
            )
        failures = capture_templates.get("failures") or []
        if failures:
            lines.extend(["", "Failures:", ""])
            lines.extend(f"- {failure}" for failure in failures)
    checklist = report.get("fixture_bench_checklist") or []
    if checklist:
        lines.extend(
            [
                "",
                "## Fixture Bench Checklist",
                "",
                "| Gate | Instrument | Setup | Input Template | Capture | Pass Criteria |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in checklist:
            input_template = item.get("input_template_command") or ""
            lines.append(
                f"| {item['gate']} {item['name']} | {item.get('instrument') or ''} | "
                f"{item.get('setup') or ''} | `{input_template}` | {item.get('capture') or ''}<br>"
                f"{item.get('minimum_evidence') or ''} | {item.get('pass_criteria') or ''} |"
            )
    pytest_report = report.get("pytest")
    power_report = report.get("power_check")
    packet_reports = report.get("packet_smokes") or (
        [report["packet_smoke"]] if report.get("packet_smoke") else []
    )
    if power_report:
        lines.extend(
            [
                "",
                "## Board Power Check",
                "",
                f"Pass: `{str(power_report['pass']).lower()}`",
                "",
                "| Port | Pass | Power dBm | Raw Bytes | Raw SHA-256 | Notes |",
                "|---|---|---:|---:|---|---|",
            ]
        )
        for item in power_report["boards"]:
            lines.append(
                f"| {item['port']} | {str(item['pass']).lower()} | "
                f"{'' if item['power_dbm'] is None else item['power_dbm']} | "
                f"{item.get('raw_bytes', '')} | "
                f"`{item.get('raw_sha256', '')}` | "
                f"{'<br>'.join(item['failures'])} |"
            )
    if packet_reports:
        packet_pass = all(item["pass"] for item in packet_reports)
        lines.extend(
            [
                "",
                "## Packet Smoke",
                "",
                f"Pass: `{str(packet_pass).lower()}`",
            ]
        )
        for packet_report in packet_reports:
            lines.extend(
                [
                    "",
                    (
                        f"Path: `{packet_report['tx_port']} -> "
                        f"{packet_report['rx_port']}` on RF path "
                        f"`{packet_report['rf_path']}`"
                    ),
                    f"Packets requested: `{packet_report['packets']}`",
                    f"Return code: `{packet_report['returncode']}`",
                    "",
                    "| Metric | Value |",
                    "|---|---:|",
                ]
            )
            evidence = packet_report.get("evidence") or {}
            for key in (
                "rx_packet_lines",
                "rx_count",
                "rx_crc_err_drop",
                "rx_overflow",
                "tx_transmitted",
                "tx_user_tx_started",
            ):
                if key in evidence:
                    lines.append(f"| {key} | {evidence[key]} |")
            log_artifacts = [
                ("RX", evidence.get("rx_log_artifact")),
                ("TX", evidence.get("tx_log_artifact")),
            ]
            if any(isinstance(artifact, dict) and artifact.get("exists") for _label, artifact in log_artifacts):
                lines.extend(
                    [
                        "",
                        "| Log | Path | Bytes | SHA-256 | Modified UTC |",
                        "|---|---|---:|---|---|",
                    ]
                )
                for label, artifact in log_artifacts:
                    if not isinstance(artifact, dict) or artifact.get("exists") is not True:
                        continue
                    lines.append(
                        f"| {label} | `{artifact.get('path') or ''}` | "
                        f"{artifact.get('bytes') or ''} | `{artifact.get('sha256') or ''}` | "
                        f"{artifact.get('mtime_utc') or ''} |"
                    )
            failures = packet_report.get("evidence_failures") or []
            if failures:
                lines.extend(["", "Evidence failures:"])
                lines.extend(f"- {failure}" for failure in failures)
            lines.extend(
                [
                    "",
                    "```text",
                    packet_report["stdout"].strip(),
                    "```",
                ]
            )
    if pytest_report:
        lines.extend(
            [
                "",
                "## Software Tests",
                "",
                f"Pass: `{str(pytest_report['pass']).lower()}`",
                f"Return code: `{pytest_report['returncode']}`",
                "",
                "```text",
                pytest_report["stdout"].strip(),
                "```",
            ]
        )
    lines.extend(["", "## Audit", "", render_audit_markdown(audit_report).strip(), ""])
    return "\n".join(lines)


def render_bench_checklist_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Prototype 0 Fixture Bench Checklist",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
    ]
    for item in report.get("fixture_bench_checklist") or []:
        lines.extend(
            [
                f"## {item['gate']} {item['name']}",
                "",
                f"- External input: {item.get('external_input') or ''}",
                f"- Instrument: {item.get('instrument') or ''}",
                f"- Setup: {item.get('setup') or ''}",
                f"- Capture artifact: {item.get('capture') or ''}",
                f"- Minimum evidence: {item.get('minimum_evidence') or ''}",
                f"- Pass criteria: {item.get('pass_criteria') or ''}",
                f"- Input template command: `{item.get('input_template_command') or ''}`",
                "",
                "```powershell",
                item.get("input_template_command") or "",
                item.get("prepare_command") or "",
                item.get("fill_command") or "",
                item.get("verify_command") or "",
                item.get("execute_command") or "",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_status_mermaid(report: dict[str, Any]) -> str:
    completion = report.get("completion_audit") or {}
    gates = completion.get("gates") or []
    class_by_gate = {
        gate["gate"]: gate.get("classification", "not-proved")
        for gate in gates
        if isinstance(gate, dict)
    }
    lines = [
        "flowchart LR",
        '  classDef proved fill:#d1fae5,stroke:#047857,color:#064e3b',
        '  classDef external fill:#fef3c7,stroke:#b45309,color:#78350f',
        '  classDef notproved fill:#f3e8ff,stroke:#7e22ce,color:#581c87',
        '  classDef summary fill:#e0f2fe,stroke:#0369a1,color:#0c4a6e',
    ]
    previous_node = None
    for gate in report["audit"]["gates"]:
        gate_id = gate["gate"]
        node = gate_id.replace("-", "")
        classification = class_by_gate.get(gate_id, "not-proved")
        class_name = "notproved" if classification == "not-proved" else classification
        evidence_count = sum(1 for item in gate.get("evidence") or [] if item.get("exists"))
        evidence_total = len(gate.get("evidence") or [])
        readiness = gate.get("readiness")
        readiness_line = f"\\nreadiness: {readiness['status']}" if readiness else ""
        label = (
            f"{gate_id}\\n{gate['name']}\\n"
            f"{classification}\\n"
            f"status: {gate['status']}\\n"
            f"evidence: {evidence_count}/{evidence_total}"
            f"{readiness_line}"
        )
        lines.append(f'  {node}["{label}"]')
        if previous_node is not None:
            lines.append(f"  {previous_node} --> {node}")
        lines.append(f"  class {node} {class_name}")
        previous_node = node

    summary = completion.get("summary") or {}
    lines.append(
        '  Completion["'
        f"complete: {str(completion.get('prototype0_complete')).lower()}\\n"
        f"proved: {summary.get('proved', 0)} / external: {summary.get('external', 0)} / "
        f"not-proved: {summary.get('not_proved', 0)}\\n"
        f"all remaining external: {str(completion.get('all_remaining_work_external')).lower()}"
        '"]'
    )
    if previous_node is not None:
        lines.append(f"  {previous_node} --> Completion")
    lines.append("  class Completion summary")
    return "\n".join(lines) + "\n"


def status_output_manifest(
    *,
    report: dict[str, Any],
    json_path: Path | None = None,
    markdown_path: Path | None = None,
    mermaid_path: Path | None = None,
    bench_checklist_path: Path | None = None,
) -> dict[str, Any]:
    outputs = []
    for kind, path in (
        ("json", json_path),
        ("markdown", markdown_path),
        ("mermaid", mermaid_path),
        ("bench_checklist", bench_checklist_path),
    ):
        if path is None:
            continue
        artifact = _file_artifact(path)
        artifact["kind"] = kind
        outputs.append(artifact)
    return {
        "schema": "prototype0-status-output-manifest-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status_generated_at": report.get("generated_at"),
        "status_pass": report.get("pass"),
        "outputs": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run repeatable Prototype 0 software/audit/fixture status checks."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--pytest", action="store_true", help="run simulator and tools tests")
    parser.add_argument(
        "--power-check",
        action="store_true",
        help="query getPower on each configured board serial port",
    )
    parser.add_argument(
        "--power-port",
        action="append",
        dest="power_ports",
        help="board serial port for --power-check; repeatable, defaults to COM8 and COM10",
    )
    parser.add_argument(
        "--packet-smoke",
        action="store_true",
        help="run a short two-board RF path 0 packet smoke",
    )
    parser.add_argument("--packet-rx-port", default=DEFAULT_PACKET_RX_PORT)
    parser.add_argument("--packet-tx-port", default=DEFAULT_PACKET_TX_PORT)
    parser.add_argument("--packet-rf-path", type=int, choices=(0, 1), default=DEFAULT_RF_PATH)
    parser.add_argument("--packet-count", type=int, default=DEFAULT_PACKET_COUNT)
    parser.add_argument(
        "--packet-bidirectional",
        action="store_true",
        help="with --packet-smoke, also run the reversed TX/RX direction",
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--mermaid", type=Path)
    parser.add_argument(
        "--bench-checklist",
        type=Path,
        help="write a standalone Markdown checklist for external fixture capture gates",
    )
    args = parser.parse_args()

    report = run_status(
        root=args.root,
        run_pytest=args.pytest,
        power_check=args.power_check,
        power_ports=tuple(args.power_ports or DEFAULT_POWER_PORTS),
        packet_smoke=args.packet_smoke,
        packet_rx_port=args.packet_rx_port,
        packet_tx_port=args.packet_tx_port,
        packet_rf_path=args.packet_rf_path,
        packet_count=args.packet_count,
        packet_bidirectional=args.packet_bidirectional,
    )
    rendered_json = json.dumps(report, indent=2, sort_keys=True)
    print(render_markdown(report))
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered_json + "\n", encoding="utf-8")
    if args.markdown is not None:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    if args.mermaid is not None:
        args.mermaid.parent.mkdir(parents=True, exist_ok=True)
        args.mermaid.write_text(render_status_mermaid(report), encoding="utf-8")
    if args.bench_checklist is not None:
        args.bench_checklist.parent.mkdir(parents=True, exist_ok=True)
        args.bench_checklist.write_text(render_bench_checklist_markdown(report), encoding="utf-8")
    if args.json is not None:
        manifest = status_output_manifest(
            report=report,
            json_path=args.json,
            markdown_path=args.markdown,
            mermaid_path=args.mermaid,
            bench_checklist_path=args.bench_checklist,
        )
        manifest_path = args.json.with_name(args.json.stem + "-artifacts.json")
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
