import json
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from audit_prototype0_gates import DEFAULT_ROLLUP_DOC, GATES
import prototype0_status_run
from prototype0_status_run import (
    external_actions,
    fixture_action_plan,
    fixture_bench_checklist,
    fixture_capture_template_status,
    fixture_input_inventory,
    fixture_non_closure_guardrails,
    parse_packet_smoke_stdout,
    parse_power_deci_dbm,
    render_bench_checklist_markdown,
    render_markdown,
    render_status_mermaid,
    run_status,
    summarize_packet_smoke_logs,
    status_output_manifest,
    validate_packet_smoke_evidence,
)


SCRIPT = Path(__file__).parents[1] / "prototype0_status_run.py"
CAPTURE_TEMPLATE_SCRIPT = Path(__file__).parents[1] / "prototype0_fixture_capture_templates.py"


def _retention_summary(packets: int = 200) -> dict[str, object]:
    return {
        "pass": True,
        "packets": packets,
        "directions": [
            {
                "pass": True,
                "tx_port": "COM10",
                "rx_port": "COM8",
                "summary": {
                    "requested_packets": packets,
                    "transmitted_packets": packets,
                    "rx_count": packets,
                    "sync_detect": packets,
                    "rx_crc_drop": 0,
                    "tx_failed_packets": 0,
                    "delivery_ratio": 1.0,
                },
            },
            {
                "pass": True,
                "tx_port": "COM8",
                "rx_port": "COM10",
                "summary": {
                    "requested_packets": packets,
                    "transmitted_packets": packets,
                    "rx_count": packets,
                    "sync_detect": packets,
                    "rx_crc_drop": 0,
                    "tx_failed_packets": 0,
                    "delivery_ratio": 1.0,
                },
            },
        ],
    }


def _write_manifest_files(root: Path) -> None:
    rollup_refs = []
    rollup_blockers = []
    for gate in GATES:
        for evidence in gate.evidence:
            path = root / evidence.path
            path.parent.mkdir(parents=True, exist_ok=True)
            if evidence.kind == "json":
                if evidence.validator == "railtest_bidirectional_retention":
                    data = _retention_summary()
                else:
                    data = {"pass": True}
                path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            else:
                path.write_text("# evidence\n", encoding="utf-8")
            if evidence.kind == "doc" and evidence.path.endswith(".md"):
                rollup_refs.append(Path(evidence.path).name)
        rollup_blockers.extend(gate.blockers)
    (root / DEFAULT_ROLLUP_DOC).write_text(
        "\n".join(f"- `{name}`" for name in rollup_refs)
        + "\n"
        + "\n".join(f"- {blocker}" for blocker in rollup_blockers)
        + "\n",
        encoding="utf-8",
    )


def _write_ready_fixture_metadata(root: Path) -> None:
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "20260808-e0-03-readiness.json").write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-readiness-v1",
                "gate": "E0-03",
                "instrument": "Saleae Logic Pro 8",
                "ground_connected": True,
                "sample_rate_hz": 5_000_000,
                "channels": {"queue": "PB3", "start": "PB2"},
                "expected_samples": 100,
                "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv",
                "analyzer_flags": ["--fail-on-unpaired-edges"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "20260808-e0-05-readiness.json").write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-readiness-v1",
                "gate": "E0-05",
                "method": "Mini-Circuits 30 dB inline attenuator or shield box",
                "rf_path": 0,
                "same_direction_all_steps": True,
                "packet_count_per_step": 200,
                "physical_setup_note": "RF path 0, COM10-to-COM8 direction, same antenna geometry for baseline and attenuated steps.",
                "baseline_summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
                "attenuated_steps": [
                    {
                        "label": "30dB",
                        "physical_setting": "30 dB inline attenuator",
                        "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "20260808-e0-05-step-00-baseline.json").write_text(
        json.dumps(
            {
                "pass": True,
                "requested_packets": 200,
                "transmitted_packets": 200,
                "rx_count": 200,
                "delivery_ratio": 1.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "20260808-e0-07-readiness.json").write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-readiness-v1",
                "gate": "E0-07",
                "fixture_method": "wired DAC output to ADC capture input loopback",
                "firmware_timing_markers": True,
                "expected_samples": 10,
                "target_latency_ms": 120,
                "max_latency_ms": 180,
                "output_csv": "firmware/prototype0/fg23/results/20260808-e0-07-audio-loopback.csv",
                "events": [
                    "capture_frame",
                    "impulse",
                    "packet_queue",
                    "playback_output",
                    "rx_done",
                    "tx_start",
                ],
                "event_aliases": {
                    "capture": "capture_frame",
                    "impulse": "impulse",
                    "playback": "playback_output",
                    "queue": "packet_queue",
                    "rx": "rx_done",
                    "tx_start": "tx_start",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_status_run_treats_missing_fixture_inputs_as_expected(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    report = run_status(root=tmp_path)

    assert report["pass"] is True
    assert report["audit"]["summary"]["problem"] == 0
    assert {item["status"] for item in report["fixture_dry_runs"]} == {"no-readiness"}
    assert all(item["expected_external_input"] for item in report["fixture_dry_runs"])
    assert [item["gate"] for item in report["external_actions"]] == [
        "E0-03",
        "E0-05",
        "E0-07",
    ]


def test_status_run_reports_template_readiness_when_no_live_readiness(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    template_path = tmp_path / "results/20260808-e0-03-readiness-template.json"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(
        json.dumps(
            {
                "gate": "E0-03",
                "instrument": "logic analyzer or oscilloscope model",
                "ground_connected": False,
                "sample_rate_hz": 5_000_000,
                "channels": {"queue": "PB3", "start": "PB2"},
                "expected_samples": 100,
                "output_csv": "firmware/prototype0/fg23/results/YYYYMMDD-e0-03-scheduled-tx-gpio.csv",
                "analyzer_flags": ["--fail-on-unpaired-edges"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = run_status(root=tmp_path)

    e0_03 = next(item for item in report["fixture_dry_runs"] if item["gate"] == "E0-03")
    assert e0_03["status"] == "no-readiness"
    assert e0_03["readiness"] == "results/20260808-e0-03-readiness-template.json"
    assert e0_03["audit_readiness_status"] == "not-ready"
    assert any("latest manifest readiness" in failure for failure in e0_03["failures"])


def test_fixture_input_inventory_reports_present_and_missing_inputs(tmp_path: Path) -> None:
    reports = [
        {
            "gate": "E0-05",
            "status": "dry-run",
            "readiness": "firmware/prototype0/fg23/results/20260808-e0-05-readiness.json",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-attenuation-summary.json",
            "expected_external_input": True,
            "inputs": [
                {
                    "path": "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
                    "exists": True,
                    "bytes": 123,
                    "sha256": "a" * 64,
                    "mtime_utc": "2026-08-08T00:00:00+00:00",
                },
                {
                    "path": "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
                    "exists": False,
                    "bytes": None,
                    "sha256": None,
                    "mtime_utc": None,
                },
            ],
        }
    ]

    inventory = fixture_input_inventory(reports)

    assert inventory == [
        {
            "gate": "E0-05",
            "status": "dry-run",
            "readiness": "firmware/prototype0/fg23/results/20260808-e0-05-readiness.json",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-attenuation-summary.json",
            "inputs_present": 1,
            "inputs_total": 2,
            "present_inputs": [
                "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json"
            ],
            "missing_inputs": [
                "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json"
            ],
            "input_artifacts": [
                {
                    "path": "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
                    "exists": True,
                    "bytes": 123,
                    "sha256": "a" * 64,
                    "mtime_utc": "2026-08-08T00:00:00+00:00",
                },
                {
                    "path": "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
                    "exists": False,
                    "bytes": None,
                    "sha256": None,
                    "mtime_utc": None,
                },
            ],
            "all_inputs_present": False,
            "expected_external_input": True,
        }
    ]


def test_fixture_non_closure_guardrails_name_substitute_prechecks() -> None:
    guardrails = fixture_non_closure_guardrails()
    by_gate = {item["gate"]: item for item in guardrails}

    assert set(by_gate) == {"E0-03", "E0-05", "E0-07"}
    assert "fixture run report" in by_gate["E0-03"]["accepted_closure_evidence"]
    assert any(
        "SDK timestamp" in item
        for item in by_gate["E0-03"]["non_closing_prechecks"]
    )
    assert any(
        "TX-power" in item
        for item in by_gate["E0-05"]["non_closing_prechecks"]
    )
    assert any(
        "RF path 1" in item
        for item in by_gate["E0-05"]["non_closing_prechecks"]
    )
    assert any(
        "capture-template" in item
        for item in by_gate["E0-07"]["non_closing_prechecks"]
    )


def test_status_run_fails_on_audit_problem(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    (tmp_path / "20260807-openref-runtime-capacity-result.md").unlink()

    report = run_status(root=tmp_path)

    assert report["pass"] is False
    assert report["audit"]["summary"]["problem"] == 1


def test_parse_power_deci_dbm() -> None:
    assert parse_power_deci_dbm("{{(getPower)}{powerLevel:185}{power:140}}") == 140
    assert parse_power_deci_dbm("{{(getPower)}{power:-4}}") == -4
    assert parse_power_deci_dbm("{{(status)}}") is None


def test_external_actions_summarizes_incomplete_gates(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = run_status(root=tmp_path)

    actions = external_actions(report["audit"])

    assert [item["gate"] for item in actions] == ["E0-03", "E0-05", "E0-07"]
    assert actions[0]["status"] == "partial"
    assert actions[1]["status"] == "blocked"
    assert actions[0]["run_report_status"] == "missing"
    assert actions[0]["external_blocker"] is True
    assert actions[0]["blocker_type"] == "external-fixture"
    assert actions[0]["fixture_evidence_promoted"] is False
    assert actions[0]["fixture_promotion_failures"] == ["fixture runner report is missing"]
    assert "logic-analyzer" in actions[0]["blockers"][0]
    assert "--gate E0-03 --fill" in actions[0]["next_command"]
    assert "YYYYMMDD" not in actions[0]["next_command"]
    assert "20260808-e0-03-readiness.json" in actions[0]["next_command"]


def test_fixture_action_plan_summarizes_bench_commands(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = run_status(root=tmp_path)

    plan = fixture_action_plan(report["audit"])

    assert [item["gate"] for item in plan] == ["E0-03", "E0-05", "E0-07"]
    assert plan[0]["template_command"].startswith(
        "python tools/prototype0_fixture_readiness.py --gate E0-03 --template"
    )
    assert "20260808-e0-03-readiness-template.json" in plan[0]["template_command"]
    assert "YYYYMMDD" not in plan[0]["template_command"]
    assert "run_prototype0_fixture_analysis.py --readiness" in plan[0]["dry_run_command"]
    assert "run_prototype0_fixture_analysis.py --readiness" in plan[0]["run_command"]
    assert "20260808-e0-03-readiness.json --dry-run" in plan[0]["dry_run_command"]
    assert "20260808-e0-03-readiness.json --json" in plan[0]["run_command"]
    assert "20260808-e0-03-run-report.json" in plan[0]["run_command"]
    assert "--gate E0-03 --fill" in plan[0]["fill_command"]
    assert "--attenuated-step" in plan[1]["fill_command"]
    assert "20260808-e0-05-readiness.json --dry-run" in plan[1]["dry_run_command"]
    assert "20260808-e0-05-readiness-template.json" in plan[1]["template_command"]
    assert "YYYYMMDD" not in plan[1]["template_command"]
    assert "20260808-e0-05-run-report.json" in plan[1]["run_command"]
    assert "firmware_timing_markers=true" in plan[2]["fill_command"]
    assert "20260808-e0-07-readiness-template.json" in plan[2]["template_command"]
    assert "YYYYMMDD" not in plan[2]["template_command"]
    assert "20260808-e0-07-readiness.json --dry-run" in plan[2]["dry_run_command"]
    assert "20260808-e0-07-run-report.json" in plan[2]["run_command"]
    assert plan[0]["external_blocker"] is True
    assert plan[0]["blocker_type"] == "external-fixture"
    assert "logic-analyzer" in plan[0]["external_input"]
    assert plan[0]["fixture_evidence_promoted"] is False
    assert plan[0]["fixture_promotion_failures"] == ["fixture runner report is missing"]


def test_fixture_action_plan_fill_commands_are_concrete(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = run_status(root=tmp_path)

    fill_commands = [
        item["fill_command"].lower() for item in fixture_action_plan(report["audit"])
    ]
    template_commands = [
        item["template_command"].lower() for item in fixture_action_plan(report["audit"])
    ]

    assert all("yyyy" not in command for command in fill_commands)
    assert all("yyyy" not in command for command in template_commands)
    assert all("describe" not in command for command in fill_commands)
    assert all("model" not in command for command in fill_commands)
    assert all("electrical or acoustic" not in command for command in fill_commands)
    assert "physical_setting=30 db inline attenuator" in fill_commands[1]
    assert "wired dac output to adc capture input loopback" in fill_commands[2]


def test_status_run_includes_fixture_action_plan(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    report = run_status(root=tmp_path)

    assert [item["gate"] for item in report["fixture_action_plan"]] == [
        "E0-03",
        "E0-05",
        "E0-07",
    ]


def test_status_run_summarizes_only_external_blockers(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    report = run_status(root=tmp_path)

    summary = report["external_blocker_summary"]
    assert summary["only_external_blockers"] is True
    assert summary["incomplete_gates"] == ["E0-03", "E0-05", "E0-07"]
    assert summary["external_blocked_gates"] == ["E0-03", "E0-05", "E0-07"]
    assert summary["unclassified_incomplete_gates"] == []
    assert summary["evidence_problem_count"] == 0
    assert summary["missing_input_count"] == 0
    assert summary["all_missing_inputs"] == []


def test_status_run_summarizes_ready_fixture_missing_inputs(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    _write_ready_fixture_metadata(tmp_path)

    report = run_status(root=tmp_path)

    summary = report["external_blocker_summary"]
    assert summary["only_external_blockers"] is True
    assert summary["missing_input_count"] == 3
    assert [Path(path).name for path in summary["all_missing_inputs"]] == [
        "20260808-e0-03-scheduled-tx-gpio.csv",
        "20260808-e0-05-step-01-30db.json",
        "20260808-e0-07-audio-loopback.csv",
    ]
    assert [Path(path).name for path in summary["missing_inputs_by_gate"]["E0-05"]] == [
        "20260808-e0-05-step-01-30db.json"
    ]
    assert [Path(path).name for path in summary["present_inputs_by_gate"]["E0-05"]] == [
        "20260808-e0-05-step-00-baseline.json"
    ]
    e0_05_artifacts = summary["present_artifacts_by_gate"]["E0-05"]
    assert [Path(item["path"]).name for item in e0_05_artifacts] == [
        "20260808-e0-05-step-00-baseline.json"
    ]
    assert e0_05_artifacts[0]["bytes"] > 0
    assert len(e0_05_artifacts[0]["sha256"]) == 64
    assert Path(summary["summary_outputs_by_gate"]["E0-07"]).name == (
        "20260808-e0-07-audio-loopback.summary.json"
    )


def test_status_run_includes_completion_audit(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    report = run_status(root=tmp_path)

    completion = report["completion_audit"]
    assert completion["prototype0_complete"] is False
    assert completion["all_remaining_work_external"] is True
    assert completion["proved_gates"] == ["E0-01", "E0-02", "E0-04", "E0-06"]
    assert completion["external_gates"] == ["E0-03", "E0-05", "E0-07"]
    assert completion["not_proved_gates"] == []
    assert completion["summary"] == {
        "proved": 4,
        "external": 3,
        "not_proved": 0,
        "total": 7,
    }
    e0_05 = next(gate for gate in completion["gates"] if gate["gate"] == "E0-05")
    assert e0_05["classification"] == "external"
    assert e0_05["complete"] is False
    assert "external fixture evidence" in e0_05["reason"]
    assert "fixture runner report is missing" in e0_05["reason"]
    assert e0_05["fixture_evidence_promoted"] is False
    assert e0_05["fixture_promotion_failures"] == ["fixture runner report is missing"]


def test_fixture_bench_checklist_adds_capture_details(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = run_status(root=tmp_path)

    checklist = fixture_bench_checklist(report["fixture_action_plan"])

    assert [item["gate"] for item in checklist] == ["E0-03", "E0-05", "E0-07"]
    assert checklist[0]["external_blocker"] is True
    assert checklist[0]["blocker_type"] == "external-fixture"
    assert "PB3 queue marker" in checklist[0]["setup"]
    assert "prototype0_fixture_capture_templates.py --gate E0-03" in checklist[0]["input_template_command"]
    assert "--gate E0-03 --fill" in checklist[0]["fill_command"]
    assert "packet summary JSON" in checklist[1]["capture"]
    assert "prototype0_fixture_capture_templates.py --gate E0-05" in checklist[1]["input_template_command"]
    assert "--attenuated-step" in checklist[1]["fill_command"]
    assert "impulse-to-playback" in checklist[2]["minimum_evidence"]
    assert "prototype0_fixture_capture_templates.py --gate E0-07" in checklist[2]["input_template_command"]
    assert "firmware_timing_markers=true" in checklist[2]["fill_command"]


def test_status_run_includes_fixture_bench_checklist(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    report = run_status(root=tmp_path)

    assert [item["gate"] for item in report["fixture_bench_checklist"]] == [
        "E0-03",
        "E0-05",
        "E0-07",
    ]
    assert report["fixture_bench_checklist"][0]["external_blocker"] is True
    assert report["fixture_bench_checklist"][0]["blocker_type"] == "external-fixture"
    assert "logic analyzer" in report["fixture_bench_checklist"][0]["instrument"]
    assert "prototype0_fixture_capture_templates.py" in report["fixture_bench_checklist"][0]["input_template_command"]
    assert report["fixture_capture_templates"]["pass"] is False
    assert "manifest missing" in report["fixture_capture_templates"]["failures"]


def test_fixture_capture_template_status_validates_generated_templates(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    output_dir = root / "templates/fixture-captures"
    subprocess.run(
        [
            sys.executable,
            str(CAPTURE_TEMPLATE_SCRIPT),
            "--gate",
            "all",
            "--output-dir",
            str(output_dir),
            "--json",
            str(output_dir / "capture-template-manifest.json"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    status = fixture_capture_template_status(root)

    assert status["pass"] is True
    assert status["failures"] == []
    assert len(status["files"]) == 4
    assert all(item["exists"] for item in status["files"])
    assert all(item["content_matches"] for item in status["files"])


def test_status_run_includes_power_check(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_query_power(port: str, *, baud: int = 115200):
        return {
            "port": port,
            "pass": True,
            "power_deci_dbm": 100 if port == "COM8" else 140,
            "power_dbm": 10.0 if port == "COM8" else 14.0,
            "raw": f"{{{{(getPower)}}{{power:{100 if port == 'COM8' else 140}}}}}",
            "failures": [],
        }

    monkeypatch.setattr(prototype0_status_run, "_query_power", fake_query_power)

    report = run_status(root=tmp_path, power_check=True, power_ports=("COM8", "COM10"))

    assert report["pass"] is True
    assert report["power_check"]["pass"] is True
    assert [item["power_dbm"] for item in report["power_check"]["boards"]] == [10.0, 14.0]
    assert all(item["raw_bytes"] > 0 for item in report["power_check"]["boards"])
    assert all(len(item["raw_sha256"]) == 64 for item in report["power_check"]["boards"])


def test_status_run_fails_on_power_check_failure(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_query_power(port: str, *, baud: int = 115200):
        return {
            "port": port,
            "pass": False,
            "power_deci_dbm": None,
            "power_dbm": None,
            "raw": "",
            "failures": ["port unavailable"],
        }

    monkeypatch.setattr(prototype0_status_run, "_query_power", fake_query_power)

    report = run_status(root=tmp_path, power_check=True, power_ports=("COM8",))

    assert report["pass"] is False
    assert report["power_check"]["boards"][0]["failures"] == ["port unavailable"]


def test_status_run_includes_packet_smoke(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 0,
            "pass": True,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": "PASS: packet exchange observed (20 TX request)\n",
            "stderr": "",
            "evidence": {
                "rx_packet_lines": 20,
                "rx_count": 20,
                "rx_crc_err_drop": 0,
                "rx_overflow": 0,
                "tx_transmitted": 20,
                "tx_user_tx_started": 20,
            },
            "evidence_failures": [],
            "output_label": output_label,
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)

    report = run_status(root=tmp_path, packet_smoke=True)

    assert report["pass"] is True
    assert report["packet_smoke"]["pass"] is True
    assert report["packet_smoke"]["rx_port"] == "COM8"
    assert report["packet_smoke"]["tx_port"] == "COM10"
    assert len(report["packet_smokes"]) == 1


def test_status_run_includes_bidirectional_packet_smoke(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)
    calls = []

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        calls.append((rx_port, tx_port, output_label))
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 0,
            "pass": True,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": "PASS: packet exchange observed (20 TX request)\n",
            "stderr": "",
            "evidence": {
                "rx_packet_lines": 20,
                "rx_count": 20,
                "rx_crc_err_drop": 0,
                "rx_overflow": 0,
                "tx_transmitted": 20,
                "tx_user_tx_started": 20,
            },
            "evidence_failures": [],
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)

    report = run_status(root=tmp_path, packet_smoke=True, packet_bidirectional=True)

    assert report["pass"] is True
    assert [(item["rx_port"], item["tx_port"]) for item in report["packet_smokes"]] == [
        ("COM8", "COM10"),
        ("COM10", "COM8"),
    ]
    assert report["packet_smoke"] == report["packet_smokes"][0]
    assert calls[0][2].endswith("-01-COM10-to-COM8")
    assert calls[1][2].endswith("-02-COM8-to-COM10")


def test_status_run_fails_on_reverse_packet_smoke_failure(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        passed = rx_port == "COM8"
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 0 if passed else 1,
            "pass": passed,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": "PASS\n" if passed else "FAIL\n",
            "stderr": "",
            "evidence": {},
            "evidence_failures": [] if passed else ["RX log missing"],
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)

    report = run_status(root=tmp_path, packet_smoke=True, packet_bidirectional=True)

    assert report["pass"] is False
    assert report["packet_smokes"][0]["pass"] is True
    assert report["packet_smokes"][1]["pass"] is False


def test_status_run_fails_on_packet_smoke_failure(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 1,
            "pass": False,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": "FAIL: packet exchange markers missing\n",
            "stderr": "",
            "evidence": {},
            "evidence_failures": ["RX log missing"],
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)

    report = run_status(root=tmp_path, packet_smoke=True)

    assert report["pass"] is False
    assert report["packet_smoke"]["returncode"] == 1


def test_parse_packet_smoke_stdout_paths() -> None:
    parsed = parse_packet_smoke_stdout(
        "PASS: packet exchange observed (20 TX request)\n"
        "RX log: firmware\\prototype0\\fg23\\results\\20260808-railtest-pair-rx.log\n"
        "TX log: firmware\\prototype0\\fg23\\results\\20260808-railtest-pair-tx.log\n"
    )

    assert parsed["rx_log"].endswith("20260808-railtest-pair-rx.log")
    assert parsed["tx_log"].endswith("20260808-railtest-pair-tx.log")


def test_summarize_packet_smoke_logs(tmp_path: Path) -> None:
    rx_log = tmp_path / "rx.log"
    tx_log = tmp_path / "tx.log"
    rx_log.write_text(
        "{{(rxPacket)}{crc:Pass}}\n"
        "{{(rxPacket)}{crc:Pass}}\n"
        "{{(status)}{RxCount:2}{RxCrcErrDrop:0}{RxOverflow:0}}\n",
        encoding="utf-8",
    )
    tx_log.write_text(
        "{{(txEnd)}{txStatus:Complete}{transmitted:2}}\n"
        "{{(status)}{UserTxStarted:2}}\n",
        encoding="utf-8",
    )

    summary = summarize_packet_smoke_logs(rx_log, tx_log)

    assert summary["rx_packet_lines"] == 2
    assert summary["rx_count"] == 2
    assert summary["rx_crc_err_drop"] == 0
    assert summary["rx_overflow"] == 0
    assert summary["tx_transmitted"] == 2
    assert summary["tx_user_tx_started"] == 2
    assert summary["rx_log_artifact"]["exists"] is True
    assert summary["rx_log_artifact"]["bytes"] > 0
    assert len(summary["rx_log_artifact"]["sha256"]) == 64
    assert summary["tx_log_artifact"]["exists"] is True
    assert len(summary["tx_log_artifact"]["sha256"]) == 64


def test_validate_packet_smoke_evidence() -> None:
    evidence = {
        "rx_log_exists": True,
        "tx_log_exists": True,
        "rx_packet_lines": 20,
        "rx_count": 20,
        "rx_crc_err_drop": 0,
        "rx_overflow": 0,
        "tx_transmitted": 20,
        "tx_user_tx_started": 20,
    }

    assert validate_packet_smoke_evidence(evidence, 20) == []
    evidence["rx_count"] = 19
    evidence["rx_overflow"] = 1
    failures = validate_packet_smoke_evidence(evidence, 20)
    assert "rx_count expected 20, got 19" in failures
    assert "rx_overflow expected 0, got 1" in failures


def test_status_run_fails_when_packet_evidence_disagrees(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        evidence = {
            "rx_log_exists": True,
            "tx_log_exists": True,
            "rx_packet_lines": 20,
            "rx_count": 19,
            "rx_crc_err_drop": 0,
            "rx_overflow": 0,
            "tx_transmitted": 20,
            "tx_user_tx_started": 20,
        }
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 0,
            "pass": False,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": "PASS: packet exchange observed (20 TX request)\n",
            "stderr": "",
            "evidence": evidence,
            "evidence_failures": validate_packet_smoke_evidence(evidence, packets),
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)

    report = run_status(root=tmp_path, packet_smoke=True)

    assert report["pass"] is False
    assert "rx_count expected 20, got 19" in report["packet_smoke"]["evidence_failures"]


def test_render_markdown_includes_fixture_status(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    _write_ready_fixture_metadata(tmp_path)
    report = run_status(root=tmp_path)

    markdown = render_markdown(report)

    assert "# Prototype 0 Status Run" in markdown
    assert "## External Blocker Summary" in markdown
    assert "Only external blockers remain: `true`" in markdown
    assert "| E0-03, E0-05, E0-07 | E0-03, E0-05, E0-07 |  | 0 |" in markdown
    assert "Missing external input files: `3`" in markdown
    assert "| Gate | Missing Inputs | Expected Summary Output |" in markdown
    assert "20260808-e0-05-step-01-30db.json" in markdown
    assert "## Completion Audit" in markdown
    assert "Prototype 0 complete: `false`" in markdown
    assert "All remaining work external: `true`" in markdown
    assert "| proved | E0-01, E0-02, E0-04, E0-06 | 4 |" in markdown
    assert "| external | E0-03, E0-05, E0-07 | 3 |" in markdown
    assert "| E0-03 | dry-run |" in markdown
    assert "## Fixture Readiness Provenance" in markdown
    assert "| Gate | Readiness | Bytes | SHA-256 | Modified UTC |" in markdown
    assert "20260808-e0-03-readiness.json" in markdown
    assert "## Fixture Input Inventory" in markdown
    assert "| Gate | Inputs | Present | Missing | Summary Output |" in markdown
    assert "## Fixture Artifact Provenance" in markdown
    assert "| Gate | Input | Bytes | SHA-256 | Modified UTC |" in markdown
    assert "20260808-e0-05-step-00-baseline.json" in markdown
    assert "## Fixture Non-Closure Guardrails" in markdown
    assert "software TX-power reduction" in markdown
    assert "RF path 1 expected-negative" in markdown
    assert "## External Actions" in markdown
    assert "| Gate | Status | Readiness | Run Report | Promotion | Blocker | Next Command |" in markdown
    assert "fixture runner report is missing" in markdown
    assert "| E0-03 Scheduled transmission | partial |" in markdown
    assert "`python tools/prototype0_fixture_readiness.py --gate E0-03 --fill" in markdown
    assert "20260808-e0-03-readiness.json`" in markdown
    assert "## Fixture Action Plan" in markdown
    assert "| Gate | External Input | Prepare | Fill | Verify | Execute |" in markdown
    assert "--gate E0-03 --fill" in markdown
    assert "## Fixture Capture Templates" in markdown
    assert "Capture templates are shape examples only" in markdown
    assert "## Fixture Bench Checklist" in markdown
    assert "| Gate | Instrument | Setup | Input Template | Capture | Pass Criteria |" in markdown
    assert "| E0-05 Controlled attenuation | blocked |" in markdown
    assert "| E0-03 Scheduled transmission | External GPIO/logic-analyzer" in markdown
    assert "PB3 queue marker" in markdown
    assert "4 passed, 1 partial, 2 blocked, 0 evidence problems." in markdown


def test_render_bench_checklist_markdown(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = run_status(root=tmp_path)

    markdown = render_bench_checklist_markdown(report)

    assert markdown.startswith("# Prototype 0 Fixture Bench Checklist")
    assert "## E0-03 Scheduled transmission" in markdown
    assert "PB3 queue marker" in markdown
    assert "prototype0_fixture_capture_templates.py" in markdown
    assert "```powershell" in markdown
    assert "--gate E0-03 --fill" in markdown
    assert "--attenuated-step" in markdown
    assert "firmware_timing_markers=true" in markdown
    assert "run_prototype0_fixture_analysis.py" in markdown
    assert "20260808-e0-03-readiness.json --dry-run" in markdown
    assert "20260808-e0-03-readiness-template.json" in markdown
    assert "20260808-e0-03-run-report.json" in markdown
    assert "20260808-e0-05-readiness.json --dry-run" in markdown
    assert "20260808-e0-05-readiness-template.json" in markdown
    assert "20260808-e0-05-run-report.json" in markdown
    assert "20260808-e0-07-readiness.json --dry-run" in markdown
    assert "20260808-e0-07-readiness-template.json" in markdown
    assert "20260808-e0-07-run-report.json" in markdown


def test_render_markdown_includes_power_check(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_query_power(port: str, *, baud: int = 115200):
        return {
            "port": port,
            "pass": True,
            "power_deci_dbm": 100,
            "power_dbm": 10.0,
            "raw": "{{(getPower)}{power:100}}",
            "failures": [],
        }

    monkeypatch.setattr(prototype0_status_run, "_query_power", fake_query_power)
    report = run_status(root=tmp_path, power_check=True, power_ports=("COM8",))

    markdown = render_markdown(report)

    assert "## Board Power Check" in markdown
    assert "| Port | Pass | Power dBm | Raw Bytes | Raw SHA-256 | Notes |" in markdown
    assert "| COM8 | true | 10.0 |" in markdown
    assert report["power_check"]["boards"][0]["raw_sha256"] in markdown


def test_render_markdown_includes_packet_smoke(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 0,
            "pass": True,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": "PASS: packet exchange observed (20 TX request)\n",
            "stderr": "",
            "evidence": {
                "rx_packet_lines": 20,
                "rx_count": 20,
                "rx_crc_err_drop": 0,
                "rx_overflow": 0,
                "tx_transmitted": 20,
                "tx_user_tx_started": 20,
                "rx_log_artifact": {
                    "path": "firmware/prototype0/fg23/results/rx.log",
                    "exists": True,
                    "bytes": 100,
                    "sha256": "a" * 64,
                    "mtime_utc": "2026-08-08T00:00:00+00:00",
                },
                "tx_log_artifact": {
                    "path": "firmware/prototype0/fg23/results/tx.log",
                    "exists": True,
                    "bytes": 120,
                    "sha256": "b" * 64,
                    "mtime_utc": "2026-08-08T00:00:00+00:00",
                },
            },
            "evidence_failures": [],
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)
    report = run_status(root=tmp_path, packet_smoke=True)

    markdown = render_markdown(report)

    assert "## Packet Smoke" in markdown
    assert "Path: `COM10 -> COM8` on RF path `0`" in markdown
    assert "| rx_count | 20 |" in markdown
    assert "| Log | Path | Bytes | SHA-256 | Modified UTC |" in markdown
    assert "firmware/prototype0/fg23/results/rx.log" in markdown
    assert "PASS: packet exchange observed" in markdown


def test_render_markdown_includes_bidirectional_packet_smoke(tmp_path: Path, monkeypatch) -> None:
    _write_manifest_files(tmp_path)

    def fake_packet_smoke(*, root, rx_port, tx_port, rf_path, packets, output_label=None):
        return {
            "command": ["python", "tools/railtest_pair_smoke.py"],
            "returncode": 0,
            "pass": True,
            "rx_port": rx_port,
            "tx_port": tx_port,
            "rf_path": rf_path,
            "packets": packets,
            "stdout": f"PASS: {tx_port} to {rx_port}\n",
            "stderr": "",
            "evidence": {
                "rx_packet_lines": 20,
                "rx_count": 20,
                "rx_crc_err_drop": 0,
                "rx_overflow": 0,
                "tx_transmitted": 20,
                "tx_user_tx_started": 20,
            },
            "evidence_failures": [],
        }

    monkeypatch.setattr(prototype0_status_run, "_packet_smoke", fake_packet_smoke)
    report = run_status(root=tmp_path, packet_smoke=True, packet_bidirectional=True)

    markdown = render_markdown(report)

    assert "Path: `COM10 -> COM8` on RF path `0`" in markdown
    assert "Path: `COM8 -> COM10` on RF path `0`" in markdown
    assert "PASS: COM10 to COM8" in markdown
    assert "PASS: COM8 to COM10" in markdown


def test_render_status_mermaid_includes_completion_audit(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = run_status(root=tmp_path)

    mermaid = render_status_mermaid(report)

    assert mermaid.startswith("flowchart LR")
    assert 'E001["E0-01\\nToolchain reproduction\\nproved' in mermaid
    assert 'E003["E0-03\\nScheduled transmission\\nexternal' in mermaid
    assert "complete: false" in mermaid
    assert "all remaining external: true" in mermaid
    assert "class E005 external" in mermaid


def test_status_output_manifest_hashes_requested_outputs(tmp_path: Path) -> None:
    report = {"generated_at": "2026-08-08T00:00:00+00:00", "pass": True}
    json_path = tmp_path / "status.json"
    markdown_path = tmp_path / "status.md"
    json_path.write_text('{"pass": true}\n', encoding="utf-8")
    markdown_path.write_text("# status\n", encoding="utf-8")

    manifest = status_output_manifest(
        report=report,
        json_path=json_path,
        markdown_path=markdown_path,
    )

    assert manifest["schema"] == "prototype0-status-output-manifest-v1"
    assert manifest["status_generated_at"] == report["generated_at"]
    assert [item["kind"] for item in manifest["outputs"]] == ["json", "markdown"]
    assert all(item["exists"] is True for item in manifest["outputs"])
    assert all(len(item["sha256"]) == 64 for item in manifest["outputs"])


def test_cli_writes_outputs(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _write_manifest_files(root)
    report_json = tmp_path / "status.json"
    report_md = tmp_path / "status.md"
    report_mmd = tmp_path / "status.mmd"
    checklist_md = tmp_path / "bench-checklist.md"
    manifest_json = tmp_path / "status-artifacts.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(root),
            "--json",
            str(report_json),
            "--markdown",
            str(report_md),
            "--mermaid",
            str(report_mmd),
            "--bench-checklist",
            str(checklist_md),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Prototype 0 Status Run" in result.stdout
    assert json.loads(report_json.read_text(encoding="utf-8"))["pass"] is True
    assert report_md.read_text(encoding="utf-8").startswith("# Prototype 0 Status Run")
    mermaid = report_mmd.read_text(encoding="utf-8")
    assert mermaid.startswith("flowchart LR")
    assert "all remaining external: true" in mermaid
    assert checklist_md.read_text(encoding="utf-8").startswith(
        "# Prototype 0 Fixture Bench Checklist"
    )
    assert manifest_json.exists()
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["schema"] == "prototype0-status-output-manifest-v1"
    assert manifest["status_pass"] is True
    assert [item["kind"] for item in manifest["outputs"]] == [
        "json",
        "markdown",
        "mermaid",
        "bench_checklist",
    ]
    assert all(item["exists"] is True for item in manifest["outputs"])
    assert all(item["bytes"] > 0 for item in manifest["outputs"])
    assert all(len(item["sha256"]) == 64 for item in manifest["outputs"])
