import json
import shlex
import subprocess
import sys
from pathlib import Path
import hashlib


sys.path.insert(0, str(Path(__file__).parents[1]))

from audit_prototype0_gates import (
    DEFAULT_ROLLUP_DOC,
    GATES,
    _blocker_represented,
    _json_passes,
    audit,
    render_markdown,
    render_mermaid,
)
from prototype0_fixture_actions import (
    check_command,
    dry_run_command,
    fixture_action_details,
    run_command,
    template_command,
)
from prototype0_fixture_readiness import READINESS_SCHEMA


SCRIPT = Path(__file__).parents[1] / "audit_prototype0_gates.py"
REPO_ROOT = Path(__file__).parents[2]
FG23_PREFIX = "firmware/prototype0/fg23/"


def _retention_summary(
    *,
    packets: int = 200,
    first_rx_count: int | None = None,
    directions: int = 2,
) -> dict[str, object]:
    first_rx_count = packets if first_rx_count is None else first_rx_count
    items = [
        {
            "pass": first_rx_count == packets,
            "tx_port": "COM10",
            "rx_port": "COM8",
            "summary": {
                "requested_packets": packets,
                "transmitted_packets": packets,
                "rx_count": first_rx_count,
                "sync_detect": first_rx_count,
                "rx_crc_drop": 0,
                "tx_failed_packets": 0,
                "delivery_ratio": first_rx_count / packets,
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
    ]
    return {
        "pass": all(item["pass"] for item in items[:directions]),
        "packets": packets,
        "directions": items[:directions],
    }


def _artifact(path: Path, report_path: str) -> dict[str, object]:
    raw = path.read_bytes()
    return {
        "path": report_path,
        "exists": True,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mtime_utc": "2026-08-08T00:00:00+00:00",
    }


def _write_e0_03_readiness(root: Path) -> None:
    readiness = root / "results/20260808-e0-03-readiness.json"
    readiness.parent.mkdir(parents=True, exist_ok=True)
    readiness.write_text(
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


def _artifact_arg_for_audit_tmp(arg: str, tmp_path: Path) -> str:
    normalized = arg.replace("\\", "/")
    if normalized.startswith(FG23_PREFIX):
        return str(tmp_path / normalized[len(FG23_PREFIX):])
    return arg


def _rewrite_fixture_command_for_audit_tmp(command: str, tmp_path: Path) -> list[str]:
    args = shlex.split(command)
    rewritten: list[str] = []
    for arg in args:
        if arg == "python":
            rewritten.append(sys.executable)
        elif arg.startswith("tools/"):
            rewritten.append(str(REPO_ROOT / arg))
        elif arg.startswith(FG23_PREFIX):
            rewritten.append(_artifact_arg_for_audit_tmp(arg, tmp_path))
        else:
            rewritten.append(arg)
    if "run_prototype0_fixture_analysis.py" in Path(rewritten[1]).name and "--root" not in rewritten:
        rewritten.extend(["--root", str(tmp_path)])
    return rewritten


def _run_fixture_command_for_audit_tmp(
    command: str,
    tmp_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _rewrite_fixture_command_for_audit_tmp(command, tmp_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _write_passing_fixture_inputs_for_audit_tmp(gate: str, tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir(parents=True, exist_ok=True)
    if gate == "E0-03":
        rows = ["Time [s],Channel,Value"]
        for index in range(100):
            base = 0.000100 + index * 0.000100
            rows.extend(
                [
                    f"{base:.6f},PB3,1",
                    f"{base + 0.000001:.6f},PB3,0",
                    f"{base + 0.000004:.6f},PB2,1",
                    f"{base + 0.000005:.6f},PB2,0",
                ]
            )
        (results / "20260808-e0-03-scheduled-tx-gpio.csv").write_text(
            "\n".join(rows) + "\n",
            encoding="utf-8",
        )
    elif gate == "E0-05":
        (results / "20260808-e0-05-step-00-baseline.json").write_text(
            json.dumps(
                {
                    "requested_packets": 200,
                    "transmitted_packets": 200,
                    "rx_count": 200,
                    "delivery_ratio": 1.0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (results / "20260808-e0-05-step-01-30db.json").write_text(
            json.dumps(
                {
                    "requested_packets": 200,
                    "transmitted_packets": 200,
                    "rx_count": 180,
                    "delivery_ratio": 0.9,
                }
            )
            + "\n",
            encoding="utf-8",
        )
    elif gate == "E0-07":
        rows = ["frame_id,event,time_us"]
        for frame in range(1, 11):
            base = frame * 1_000_000
            rows.extend(
                [
                    f"{frame},impulse,{base}",
                    f"{frame},capture_frame,{base + 10_000}",
                    f"{frame},packet_queue,{base + 30_000}",
                    f"{frame},tx_start,{base + 35_000}",
                    f"{frame},rx_done,{base + 60_000}",
                    f"{frame},playback_output,{base + 90_000}",
                ]
            )
        (results / "20260808-e0-07-audio-loopback.csv").write_text(
            "\n".join(rows) + "\n",
            encoding="utf-8",
        )
    else:
        raise AssertionError(f"unsupported gate {gate}")


def test_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Prototype 0 gate evidence" in result.stdout


def test_audit_complete_manifest(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    report = audit(tmp_path)

    assert report["summary"]["passed"] == 4
    assert report["summary"]["partial"] == 1
    assert report["summary"]["blocked"] == 2
    assert report["summary"]["problem"] == 0
    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert any("--gate E0-03 --check" in action for action in e0_03["next_actions"])
    assert any("--gate E0-03 --fill" in action for action in e0_03["next_actions"])
    assert any("run_prototype0_fixture_analysis.py" in action for action in e0_03["next_actions"])
    assert any("--dry-run" in action for action in e0_03["next_actions"])
    assert any("--gate E0-03 --dry-run" in action for action in e0_03["next_actions"])
    assert any("20260808-e0-03-readiness-template.json" in action for action in e0_03["next_actions"])
    assert any("20260808-e0-03-readiness.json" in action for action in e0_03["next_actions"])
    assert not any("YYYYMMDD" in action for action in e0_03["next_actions"])
    assert e0_03["readiness"]["status"] == "missing"
    assert e0_03["run_report"]["status"] == "missing"
    assert e0_03["fixture_promotion_failures"] == ["fixture runner report is missing"]


def test_audit_promotes_external_gate_when_fixture_run_passes(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    _write_e0_03_readiness(tmp_path)
    readiness_path = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json"
    input_path = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_path.write_text("Time [s],Channel,Value\n0.0,PB3,1\n0.1,PB2,1\n", encoding="utf-8")
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "readiness": readiness_report_path,
                "readiness_artifact": _artifact(readiness_path, readiness_report_path),
                "inputs": [_artifact(input_path, input_report_path)],
                "summary_json": summary_report_path,
                "summary_artifact": _artifact(summary, summary_report_path),
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    assert report["summary"]["passed"] == 5
    assert report["summary"]["partial"] == 0
    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "passed"
    assert e0_03["fixture_evidence_promoted"] is True
    assert e0_03["blockers"] == []
    assert e0_03["next_actions"] == []


def test_audit_promotes_all_external_gates_from_published_fixture_commands(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)

    for gate in ("E0-03", "E0-05", "E0-07"):
        details = fixture_action_details(gate)
        assert details

        for command in (
            template_command(gate),
            details["fill_command"],
            check_command(gate),
            dry_run_command(gate),
        ):
            assert command is not None
            result = _run_fixture_command_for_audit_tmp(command, tmp_path)
            assert result.returncode == 0, result.stdout + result.stderr

        execute = run_command(gate)
        assert execute is not None
        missing_result = _run_fixture_command_for_audit_tmp(execute, tmp_path)
        assert missing_result.returncode == 1
        missing_json = json.loads(missing_result.stdout)
        assert missing_json["schema"] == "prototype0-fixture-run-report-v1"
        assert missing_json["gate"] == gate
        assert missing_json["status"] == "missing-inputs"

        _write_passing_fixture_inputs_for_audit_tmp(gate, tmp_path)
        passing_result = _run_fixture_command_for_audit_tmp(execute, tmp_path)
        assert passing_result.returncode == 0, passing_result.stdout + passing_result.stderr
        passing_json = json.loads(passing_result.stdout)
        assert passing_json["schema"] == "prototype0-fixture-run-report-v1"
        assert passing_json["gate"] == gate
        assert passing_json["status"] == "passed"
        assert passing_json["pass"] is True
        assert passing_json["failures"] == []
        assert Path(_artifact_arg_for_audit_tmp(details["filled_run_report"], tmp_path)).exists()

    report = audit(tmp_path)

    promoted = [
        gate
        for gate in report["gates"]
        if gate["gate"] in {"E0-03", "E0-05", "E0-07"}
    ]
    assert {gate["gate"] for gate in promoted} == {"E0-03", "E0-05", "E0-07"}
    assert all(gate["status"] == "passed" for gate in promoted)
    assert all(gate["fixture_evidence_promoted"] is True for gate in promoted)
    assert all(gate["fixture_promotion_failures"] == [] for gate in promoted)
    assert all(gate["blockers"] == [] for gate in promoted)
    assert all(gate["next_actions"] == [] for gate in promoted)
    assert report["summary"]["passed"] == 7
    assert report["summary"]["partial"] == 0
    assert report["summary"]["blocked"] == 0
    assert report["summary"]["problem"] == 0


def test_audit_does_not_promote_external_gate_when_summary_is_missing(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "summary_json": "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json",
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert any("summary JSON missing" in item for item in e0_03["fixture_promotion_failures"])


def test_audit_does_not_promote_external_gate_without_artifact_hashes(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "summary_json": "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json",
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert "run report inputs are missing" in e0_03["fixture_promotion_failures"]
    assert "run report summary_artifact is missing" in e0_03["fixture_promotion_failures"]


def test_audit_does_not_promote_external_gate_when_readiness_is_missing(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    input_path = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_path.write_text("Time [s],Channel,Value\n0.0,PB3,1\n0.1,PB2,1\n", encoding="utf-8")
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "readiness": "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json",
                "inputs": [_artifact(input_path, input_report_path)],
                "summary_json": summary_report_path,
                "summary_artifact": _artifact(summary, summary_report_path),
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert (
        "run report readiness missing: firmware/prototype0/fg23/results/20260808-e0-03-readiness.json"
        in e0_03["fixture_promotion_failures"]
    )


def test_audit_does_not_promote_external_gate_when_readiness_hash_is_stale(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    _write_e0_03_readiness(tmp_path)
    readiness_path = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json"
    readiness_artifact = _artifact(readiness_path, readiness_report_path)
    metadata = json.loads(readiness_path.read_text(encoding="utf-8"))
    metadata["sample_rate_hz"] = 6_000_000
    readiness_path.write_text(json.dumps(metadata) + "\n", encoding="utf-8")
    input_path = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_path.write_text("Time [s],Channel,Value\n0.0,PB3,1\n0.1,PB2,1\n", encoding="utf-8")
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "readiness": readiness_report_path,
                "readiness_artifact": readiness_artifact,
                "inputs": [_artifact(input_path, input_report_path)],
                "summary_json": summary_report_path,
                "summary_artifact": _artifact(summary, summary_report_path),
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert "run report readiness_artifact.sha256 does not match current file" in e0_03[
        "fixture_promotion_failures"
    ]


def test_audit_does_not_promote_external_gate_when_input_hash_is_stale(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    _write_e0_03_readiness(tmp_path)
    readiness_path = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json"
    input_path = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_path.write_text("Time [s],Channel,Value\n0.0,PB3,1\n0.1,PB2,1\n", encoding="utf-8")
    input_artifact = _artifact(input_path, input_report_path)
    input_path.write_text("Time [s],Channel,Value\n0.0,PB3,1\n0.2,PB2,1\n", encoding="utf-8")
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "readiness": readiness_report_path,
                "readiness_artifact": _artifact(readiness_path, readiness_report_path),
                "inputs": [input_artifact],
                "summary_json": summary_report_path,
                "summary_artifact": _artifact(summary, summary_report_path),
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert "run report inputs[0].sha256 does not match current file" in e0_03[
        "fixture_promotion_failures"
    ]


def test_audit_does_not_promote_external_gate_when_summary_hash_is_stale(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    _write_e0_03_readiness(tmp_path)
    readiness_path = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json"
    input_path = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.csv"
    input_path.write_text("Time [s],Channel,Value\n0.0,PB3,1\n0.1,PB2,1\n", encoding="utf-8")
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary_report_path = "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    summary_artifact = _artifact(summary, summary_report_path)
    summary.write_text(json.dumps({"pass": True, "paired_samples": 101}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "readiness": readiness_report_path,
                "readiness_artifact": _artifact(readiness_path, readiness_report_path),
                "inputs": [_artifact(input_path, input_report_path)],
                "summary_json": summary_report_path,
                "summary_artifact": summary_artifact,
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert "run report summary_artifact.sha256 does not match current file" in e0_03[
        "fixture_promotion_failures"
    ]


def test_audit_does_not_promote_external_gate_from_wrong_run_report(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "schema": "prototype0-fixture-run-report-v1",
                "generated_at": "2026-08-08T00:00:00+00:00",
                "root": str(tmp_path),
                "pass": True,
                "status": "passed",
                "gate": "E0-07",
                "summary_json": "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json",
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert e0_03["blockers"]


def test_audit_does_not_promote_external_gate_from_legacy_run_report(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    summary = tmp_path / "results/20260808-e0-03-scheduled-tx-gpio.summary.json"
    summary.write_text(json.dumps({"pass": True, "paired_samples": 100}) + "\n", encoding="utf-8")
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "summary_json": "firmware/prototype0/fg23/results/20260808-e0-03-scheduled-tx-gpio.summary.json",
                "failures": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["status"] == "partial"
    assert e0_03["fixture_evidence_promoted"] is False
    assert any("run report schema" in item for item in e0_03["fixture_promotion_failures"])
    assert any("generated_at" in item for item in e0_03["fixture_promotion_failures"])
    assert any("root" in item for item in e0_03["fixture_promotion_failures"])


def test_audit_reports_latest_ready_fixture_metadata(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    readiness = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness.write_text(
        json.dumps(
            {
                "schema": READINESS_SCHEMA,
                "gate": "E0-03",
                "instrument": "Saleae Logic Pro 8",
                "ground_connected": True,
                "sample_rate_hz": 10_000_000,
                "channels": {"queue": "PB3", "start": "PB2"},
                "expected_samples": 100,
                "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv",
                "analyzer_flags": ["--fail-on-unpaired-edges"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["readiness"]["status"] == "ready"
    assert e0_03["readiness"]["path"] == "results/20260808-e0-03-readiness.json"
    assert e0_03["readiness"]["analysis_command"][:2] == [
        "python",
        "tools/analyze_scheduled_tx_gpio.py",
    ]


def test_audit_reports_not_ready_fixture_template(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    readiness = tmp_path / "results/20260808-e0-07-readiness-template.json"
    readiness.write_text(
        json.dumps(
            {
                "schema": READINESS_SCHEMA,
                "gate": "E0-07",
                "fixture_method": "electrical or acoustic loopback method",
                "firmware_timing_markers": False,
                "expected_samples": 10,
                "target_latency_ms": 120,
                "max_latency_ms": 180,
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
                "output_csv": "firmware/prototype0/fg23/results/YYYYMMDD-e0-07-audio-loopback.csv",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_07 = next(gate for gate in report["gates"] if gate["gate"] == "E0-07")
    assert e0_07["readiness"]["status"] == "not-ready"
    assert "fixture_method is required" in e0_07["readiness"]["failures"]


def test_audit_reports_ready_fixture_artifacts_missing(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    readiness = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness.write_text(
        json.dumps(
            {
                "schema": READINESS_SCHEMA,
                "gate": "E0-03",
                "instrument": "Saleae Logic Pro 8",
                "ground_connected": True,
                "sample_rate_hz": 10_000_000,
                "channels": {"queue": "PB3", "start": "PB2"},
                "expected_samples": 100,
                "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv",
                "analyzer_flags": ["--fail-on-unpaired-edges"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    readiness_status = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")[
        "readiness"
    ]
    artifacts = readiness_status["analysis_artifacts"]
    assert artifacts["inputs_present"] == 0
    assert artifacts["inputs_total"] == 1
    assert artifacts["summary"]["exists"] is False


def test_audit_reports_ready_fixture_artifacts_pass(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    (tmp_path / "results/20260808-e0-03-gpio.csv").write_text(
        "Time,PB3,PB2\n0,0,0\n",
        encoding="utf-8",
    )
    (tmp_path / "results/20260808-e0-03-gpio.summary.json").write_text(
        json.dumps({"pass": True}) + "\n",
        encoding="utf-8",
    )
    readiness = tmp_path / "results/20260808-e0-03-readiness.json"
    readiness.write_text(
        json.dumps(
            {
                "schema": READINESS_SCHEMA,
                "gate": "E0-03",
                "instrument": "Saleae Logic Pro 8",
                "ground_connected": True,
                "sample_rate_hz": 10_000_000,
                "channels": {"queue": "PB3", "start": "PB2"},
                "expected_samples": 100,
                "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv",
                "analyzer_flags": ["--fail-on-unpaired-edges"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    readiness_status = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")[
        "readiness"
    ]
    artifacts = readiness_status["analysis_artifacts"]
    assert artifacts["inputs_present"] == 1
    assert artifacts["summary"]["exists"] is True
    assert artifacts["summary"]["pass"] is True


def test_audit_reports_latest_fixture_run_report(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    run_report = tmp_path / "results/20260808-e0-03-run-report.json"
    run_report.write_text(
        json.dumps(
            {
                "pass": True,
                "status": "passed",
                "gate": "E0-03",
                "readiness": "firmware/prototype0/fg23/results/20260808-e0-03-readiness.json",
                "summary_json": "firmware/prototype0/fg23/results/20260808-e0-03-summary.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_03 = next(gate for gate in report["gates"] if gate["gate"] == "E0-03")
    assert e0_03["run_report"]["status"] == "passed"
    assert e0_03["run_report"]["pass"] is True
    assert e0_03["run_report"]["path"] == "results/20260808-e0-03-run-report.json"
    assert e0_03["run_report"]["summary_json"].endswith("20260808-e0-03-summary.json")


def test_audit_reports_invalid_fixture_run_report(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    (tmp_path / "results/20260808-e0-07-run-report.json").write_text(
        "not-json\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    e0_07 = next(gate for gate in report["gates"] if gate["gate"] == "E0-07")
    assert e0_07["run_report"]["status"] == "invalid"
    assert "not a JSON object" in e0_07["run_report"]["failures"][0]


def test_audit_flags_missing_evidence(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    (tmp_path / "20260807-openref-runtime-capacity-result.md").unlink()

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "missing-evidence"]
    assert problem_gates[0]["gate"] == "E0-04"


def test_audit_flags_failed_json(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    (tmp_path / "results/20260807-openref-scheduled-tx-com8-summary.json").write_text(
        json.dumps({"pass": False}) + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "weak-evidence"]
    assert problem_gates[0]["gate"] == "E0-03"


def test_audit_flags_failed_retention_direction(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    summary = _retention_summary(first_rx_count=199)
    summary["pass"] = True
    (tmp_path / "results/20260808-railtest-bidirectional-retention-summary.json").write_text(
        json.dumps(summary) + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "weak-evidence"]
    assert problem_gates[0]["gate"] == "E0-01"
    assert any("directions[0].pass must be true" in item for item in problem_gates[0]["weak"])
    assert any("rx_count expected 200, got 199" in item for item in problem_gates[0]["weak"])


def test_audit_flags_incomplete_retention_directions(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    summary = _retention_summary(directions=1)
    summary["pass"] = True
    (tmp_path / "results/20260808-railtest-bidirectional-retention-summary.json").write_text(
        json.dumps(summary) + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "weak-evidence"]
    assert problem_gates[0]["gate"] == "E0-01"
    assert any("exactly two directions" in item for item in problem_gates[0]["weak"])


def test_json_passes_requires_every_list_item_to_pass() -> None:
    assert _json_passes([{"pass": True}, {"passed": True}])
    assert not _json_passes([])
    assert not _json_passes([{"pass": True}, {"pass": False}])
    assert not _json_passes([{"pass": True}, {"rx_count": 10}])


def test_blocker_represented_by_significant_terms() -> None:
    blocker = "Controlled RF attenuation, shield box, or repeatable shielding setup is still required."
    rollup = "Use an attenuator or RF shield box before final E0-05."

    assert _blocker_represented(blocker, rollup)
    assert not _blocker_represented(blocker, "All radio tests passed.")


def test_audit_flags_failed_capacity_sweep_item(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    (tmp_path / "results/20260807-openref-autorole-capacity-sweep-summary.json").write_text(
        json.dumps([{"pass": True}, {"pass": False}]) + "\n",
        encoding="utf-8",
    )

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "weak-evidence"]
    assert problem_gates[0]["gate"] == "E0-04"


def test_audit_flags_missing_rollup_reference(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    rollup = tmp_path / DEFAULT_ROLLUP_DOC
    rollup.write_text(
        rollup.read_text(encoding="utf-8").replace(
            "- `20260808-railtest-rssi-path1-negative-precheck-result.md`\n",
            "",
        ),
        encoding="utf-8",
    )

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "weak-evidence"]
    assert problem_gates[0]["gate"] == "E0-05"
    assert problem_gates[0]["missing_rollup_refs"] == [
        "20260808-railtest-rssi-path1-negative-precheck-result.md"
    ]


def test_audit_flags_missing_rollup_blocker(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    rollup = tmp_path / DEFAULT_ROLLUP_DOC
    rollup.write_text(
        rollup.read_text(encoding="utf-8").replace(
            "External GPIO/logic-analyzer or oscilloscope capture is still required.",
            "Timing evidence is fine.",
        ),
        encoding="utf-8",
    )

    report = audit(tmp_path)

    problem_gates = [gate for gate in report["gates"] if gate["status"] == "weak-evidence"]
    assert problem_gates[0]["gate"] == "E0-03"
    assert problem_gates[0]["missing_rollup_blockers"] == [
        "External GPIO/logic-analyzer or oscilloscope capture is still required."
    ]


def test_render_markdown(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = audit(tmp_path)

    markdown = render_markdown(report)

    assert "| Gate | Status | Evidence | Readiness | Run Report | Blockers | Next Actions |" in markdown
    assert "| E0-03 Scheduled transmission | partial |" in markdown
    assert "missing<br>no readiness metadata found" in markdown
    assert "missing<br>no fixture runner report found" in markdown
    assert "prototype0_fixture_readiness.py --gate E0-03 --check" in markdown
    assert "prototype0_fixture_readiness.py --gate E0-03 --fill" in markdown
    assert "run_prototype0_fixture_analysis.py --readiness" in markdown
    assert "run_prototype0_fixture_analysis.py --gate E0-03 --dry-run" in markdown
    assert "20260808-e0-03-readiness-template.json" in markdown
    assert "20260808-e0-03-readiness.json" in markdown
    assert "YYYYMMDD-e0-03-readiness" not in markdown
    assert "Summary: 4 passed, 1 partial, 2 blocked" in markdown


def test_render_mermaid(tmp_path: Path) -> None:
    _write_manifest_files(tmp_path)
    report = audit(tmp_path)

    mermaid = render_mermaid(report)

    assert mermaid.startswith("flowchart LR")
    assert 'E001["E0-01\\nToolchain reproduction\\npassed\\n6/6 evidence"]' in mermaid
    assert (
        'E003["E0-03\\nScheduled transmission\\npartial\\n'
        '4/4 evidence\\nreadiness: missing\\nrun: missing"]'
    ) in mermaid
    assert "class E005 blocked" in mermaid
    assert "4 passed / 1 partial / 2 blocked / 0 problems" in mermaid


def test_mermaid_output_file(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _write_manifest_files(root)
    output = tmp_path / "audit.mmd"

    subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--mermaid", str(output)],
        capture_output=True,
        text=True,
        check=True,
    )

    assert output.read_text(encoding="utf-8").startswith("flowchart LR")
