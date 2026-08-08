from __future__ import annotations

from typing import Any


FIXTURE_ACTION_DETAILS: dict[str, dict[str, Any]] = {
    "E0-03": {
        "template_path": "firmware/prototype0/fg23/results/20260808-e0-03-readiness-template.json",
        "filled_readiness": "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json",
        "filled_run_report": "firmware/prototype0/fg23/results/20260808-e0-03-run-report.json",
        "fill_command": 'python tools/prototype0_fixture_readiness.py --gate E0-03 --fill --set "instrument=Saleae Logic Pro 8" --set ground_connected=true --set output_csv=firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv --json firmware/prototype0/fg23/results/20260808-e0-03-readiness.json',
    },
    "E0-05": {
        "template_path": "firmware/prototype0/fg23/results/20260808-e0-05-readiness-template.json",
        "filled_readiness": "firmware/prototype0/fg23/results/20260808-e0-05-readiness.json",
        "filled_run_report": "firmware/prototype0/fg23/results/20260808-e0-05-run-report.json",
        "fill_command": 'python tools/prototype0_fixture_readiness.py --gate E0-05 --fill --set "method=Mini-Circuits 30 dB inline attenuator or shield box" --set baseline_summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json --set "physical_setup_note=RF path 0, COM10-to-COM8 direction, same antenna geometry for baseline and attenuated steps." --attenuated-step "label=30dB,physical_setting=30 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json" --json firmware/prototype0/fg23/results/20260808-e0-05-readiness.json',
    },
    "E0-07": {
        "template_path": "firmware/prototype0/fg23/results/20260808-e0-07-readiness-template.json",
        "filled_readiness": "firmware/prototype0/fg23/results/20260808-e0-07-readiness.json",
        "filled_run_report": "firmware/prototype0/fg23/results/20260808-e0-07-run-report.json",
        "fill_command": 'python tools/prototype0_fixture_readiness.py --gate E0-07 --fill --set "fixture_method=wired DAC output to ADC capture input loopback" --set firmware_timing_markers=true --set output_csv=firmware/prototype0/fg23/results/20260808-e0-07-audio-loopback.csv --json firmware/prototype0/fg23/results/20260808-e0-07-readiness.json',
    },
}


def fixture_action_details(gate: str) -> dict[str, Any]:
    return FIXTURE_ACTION_DETAILS.get(gate, {})


def template_command(gate: str) -> str | None:
    details = fixture_action_details(gate)
    template_path = details.get("template_path")
    if not template_path:
        return None
    return f"python tools/prototype0_fixture_readiness.py --gate {gate} --template --json {template_path}"


def check_command(gate: str) -> str | None:
    details = fixture_action_details(gate)
    readiness_path = details.get("filled_readiness")
    if not readiness_path:
        return None
    return f"python tools/prototype0_fixture_readiness.py --gate {gate} --check {readiness_path}"


def dry_run_command(gate: str) -> str | None:
    details = fixture_action_details(gate)
    readiness_path = details.get("filled_readiness")
    if not readiness_path:
        return None
    return f"python tools/run_prototype0_fixture_analysis.py --readiness {readiness_path} --dry-run"


def run_command(gate: str) -> str | None:
    details = fixture_action_details(gate)
    readiness_path = details.get("filled_readiness")
    report_path = details.get("filled_run_report")
    if not readiness_path or not report_path:
        return None
    return f"python tools/run_prototype0_fixture_analysis.py --readiness {readiness_path} --json {report_path}"


def discover_dry_run_command(gate: str) -> str | None:
    if not fixture_action_details(gate):
        return None
    return f"python tools/run_prototype0_fixture_analysis.py --gate {gate} --dry-run"


def discover_run_command(gate: str) -> str | None:
    details = fixture_action_details(gate)
    report_path = details.get("filled_run_report")
    if not report_path:
        return None
    return f"python tools/run_prototype0_fixture_analysis.py --gate {gate} --json {report_path}"


def concrete_next_actions(gate: str) -> tuple[str, ...] | None:
    if not fixture_action_details(gate):
        return None
    commands = (
        template_command(gate),
        check_command(gate),
        fixture_action_details(gate).get("fill_command"),
        dry_run_command(gate),
        run_command(gate),
        discover_dry_run_command(gate),
        discover_run_command(gate),
    )
    if all(command is None for command in commands):
        return None
    return tuple(command for command in commands if command)
