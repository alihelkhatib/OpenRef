import json
import shlex
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from prototype0_fixture_actions import (
    check_command,
    concrete_next_actions,
    dry_run_command,
    fixture_action_details,
    run_command,
    template_command,
)


TOOLS_DIR = Path(__file__).parents[1]
REPO_ROOT = Path(__file__).parents[2]
RESULTS_PREFIX = "firmware/prototype0/fg23/results/"


def _rewrite_command_for_tmp(command: str, tmp_path: Path) -> list[str]:
    args = shlex.split(command)
    rewritten: list[str] = []
    for arg in args:
        if arg == "python":
            rewritten.append(sys.executable)
        elif arg.startswith("tools/"):
            rewritten.append(str(REPO_ROOT / arg))
        elif arg.startswith(RESULTS_PREFIX):
            rewritten.append(str(tmp_path / arg))
        else:
            rewritten.append(arg)
    if "run_prototype0_fixture_analysis.py" in Path(rewritten[1]).name and "--root" not in rewritten:
        rewritten.extend(["--root", str(tmp_path / "firmware/prototype0/fg23")])
    return rewritten


def _run_fixture_command(command: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    args = _rewrite_command_for_tmp(command, tmp_path)
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _write_passing_fixture_inputs(gate: str, tmp_path: Path) -> None:
    results = tmp_path / RESULTS_PREFIX
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


def test_fixture_action_commands_are_concrete_for_all_external_gates() -> None:
    for gate in ("E0-03", "E0-05", "E0-07"):
        details = fixture_action_details(gate)
        actions = concrete_next_actions(gate)

        assert actions is not None
        assert template_command(gate) == actions[0]
        assert check_command(gate) == actions[1]
        assert details["fill_command"] == actions[2]
        assert dry_run_command(gate) == actions[3]
        assert run_command(gate) == actions[4]
        assert f"--gate {gate} --dry-run" in actions[5]
        assert f"--gate {gate} --json" in actions[6]
        assert not any("YYYYMMDD" in action for action in actions)
        assert any("-readiness-template.json" in action for action in actions)
        assert any("-readiness.json" in action for action in actions)
        assert any("-run-report.json" in action for action in actions)


def test_fixture_action_commands_ignore_unknown_gate() -> None:
    assert concrete_next_actions("E0-99") is None
    assert template_command("E0-99") is None
    assert check_command("E0-99") is None
    assert dry_run_command("E0-99") is None
    assert run_command("E0-99") is None


def test_fixture_action_commands_execute_to_ready_then_missing_inputs(tmp_path: Path) -> None:
    for gate in ("E0-03", "E0-05", "E0-07"):
        details = fixture_action_details(gate)
        template = template_command(gate)
        check = check_command(gate)
        dry_run = dry_run_command(gate)
        execute = run_command(gate)

        assert template is not None
        assert check is not None
        assert dry_run is not None
        assert execute is not None

        template_result = _run_fixture_command(template, tmp_path)
        assert template_result.returncode == 0, template_result.stderr
        template_json = json.loads(template_result.stdout)
        assert template_json["gate"] == gate
        assert (tmp_path / details["template_path"]).exists()

        fill_result = _run_fixture_command(details["fill_command"], tmp_path)
        assert fill_result.returncode == 0, fill_result.stdout + fill_result.stderr
        readiness_path = tmp_path / details["filled_readiness"]
        assert readiness_path.exists()
        readiness_json = json.loads(readiness_path.read_text(encoding="utf-8"))
        assert readiness_json["gate"] == gate
        assert "pass" not in readiness_json

        check_result = _run_fixture_command(check, tmp_path)
        assert check_result.returncode == 0, check_result.stdout + check_result.stderr
        check_json = json.loads(check_result.stdout)
        assert check_json["pass"] is True
        assert check_json["analysis_command_text"].startswith("python tools/")

        dry_run_result = _run_fixture_command(dry_run, tmp_path)
        assert dry_run_result.returncode == 0, dry_run_result.stdout + dry_run_result.stderr
        dry_run_json = json.loads(dry_run_result.stdout)
        assert dry_run_json["status"] == "dry-run"
        assert dry_run_json["pass"] is False
        assert any(not item["exists"] for item in dry_run_json["inputs"])

        execute_result = _run_fixture_command(execute, tmp_path)
        assert execute_result.returncode == 1
        execute_json = json.loads(execute_result.stdout)
        assert execute_json["schema"] == "prototype0-fixture-run-report-v1"
        assert execute_json["gate"] == gate
        assert execute_json["status"] == "missing-inputs"
        assert execute_json["pass"] is False
        assert execute_json["failures"][0].startswith("missing input:")
        report_json = tmp_path / details["filled_run_report"]
        assert report_json.exists()
        written_report = json.loads(report_json.read_text(encoding="utf-8"))
        assert written_report == execute_json

        _write_passing_fixture_inputs(gate, tmp_path)
        passing_result = _run_fixture_command(execute, tmp_path)
        assert passing_result.returncode == 0, passing_result.stdout + passing_result.stderr
        passing_json = json.loads(passing_result.stdout)
        assert passing_json["schema"] == "prototype0-fixture-run-report-v1"
        assert passing_json["gate"] == gate
        assert passing_json["status"] == "passed"
        assert passing_json["pass"] is True
        assert passing_json["failures"] == []
        assert passing_json["summary_json"]
        assert json.loads(report_json.read_text(encoding="utf-8")) == passing_json
