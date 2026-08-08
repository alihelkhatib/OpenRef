import json
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from run_prototype0_fixture_analysis import discover_readiness, run
from prototype0_fixture_readiness import READINESS_SCHEMA


SCRIPT = Path(__file__).parents[1] / "run_prototype0_fixture_analysis.py"


def _write_ready_audio_fixture(root: Path) -> Path:
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
    csv_path = results / "20260808-e0-07-audio.csv"
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
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    readiness = results / "20260808-e0-07-readiness.json"
    readiness.write_text(
        json.dumps(
            {
                "schema": READINESS_SCHEMA,
                "gate": "E0-07",
                "fixture_method": "wired DAC output into ADC capture fixture",
                "firmware_timing_markers": True,
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
                "output_csv": "firmware/prototype0/fg23/results/20260808-e0-07-audio.csv",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return readiness


def _write_ready_gpio_fixture(root: Path) -> Path:
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
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
    (results / "20260808-e0-03-gpio.csv").write_text(
        "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    readiness = results / "20260808-e0-03-readiness.json"
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
    return readiness


def _write_ready_attenuation_fixture(root: Path) -> Path:
    results = root / "results"
    results.mkdir(parents=True, exist_ok=True)
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
            }
        )
        + "\n",
        encoding="utf-8",
    )
    readiness = results / "20260808-e0-05-readiness.json"
    readiness.write_text(
        json.dumps(
            {
                "schema": READINESS_SCHEMA,
                "gate": "E0-05",
                "method": "Mini-Circuits VAT-30+ inline attenuator",
                "rf_path": 0,
                "same_direction_all_steps": True,
                "packet_count_per_step": 200,
                "baseline_summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
                "attenuated_steps": [
                    {
                        "label": "30dB",
                        "physical_setting": "30 dB inline attenuator",
                        "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
                    }
                ],
                "physical_setup_note": "COM10 SMA cabled through attenuator to shielded receive setup.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return readiness


def test_run_reports_missing_inputs(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)
    (root / "results/20260808-e0-07-audio.csv").unlink()

    report = run(readiness, root=root)

    assert report["status"] == "missing-inputs"
    assert report["readiness_artifact"]["exists"] is True
    assert len(report["readiness_artifact"]["sha256"]) == 64
    assert report["inputs"][0]["exists"] is False
    assert "missing input:" in report["failures"][0]


def test_run_executes_audio_analyzer(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)

    report = run(readiness, root=root)

    assert report["pass"] is True
    assert report["status"] == "passed"
    assert report["schema"] == "prototype0-fixture-run-report-v1"
    assert report["generated_at"]
    assert report["root"] == str(root)
    assert report["readiness_artifact"]["exists"] is True
    assert len(report["readiness_artifact"]["sha256"]) == 64
    assert report["readiness_artifact"]["bytes"] > 0
    assert report["summary"]["complete_samples"] == 10
    assert report["inputs"][0]["exists"] is True
    assert len(report["inputs"][0]["sha256"]) == 64
    assert report["inputs"][0]["bytes"] > 0
    assert report["summary_artifact"]["exists"] is True
    assert len(report["summary_artifact"]["sha256"]) == 64
    assert report["summary_artifact"]["bytes"] > 0
    assert (root / "results/20260808-e0-07-audio.summary.json").exists()


def test_run_executes_gpio_analyzer(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_gpio_fixture(root)

    report = run(readiness, root=root)

    assert report["pass"] is True
    assert report["status"] == "passed"
    assert report["summary"]["paired_samples"] == 100
    assert all(item["exists"] and len(item["sha256"]) == 64 for item in report["inputs"])
    assert report["summary_artifact"]["exists"] is True
    assert (root / "results/20260808-e0-03-gpio.summary.json").exists()


def test_run_executes_attenuation_analyzer(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_attenuation_fixture(root)

    report = run(readiness, root=root)

    assert report["pass"] is True
    assert report["status"] == "passed"
    assert report["summary"]["valid_steps"] == 2
    assert report["summary"]["degraded_steps"] == 1
    assert len(report["inputs"]) == 2
    assert all(item["exists"] and len(item["sha256"]) == 64 for item in report["inputs"])
    assert report["summary_artifact"]["exists"] is True


def test_run_rejects_invalid_gpio_csv_contract(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_gpio_fixture(root)
    (root / "results/20260808-e0-03-gpio.csv").write_text(
        "timestamp,wrong_channel\n0.0,1\n",
        encoding="utf-8",
    )

    def fail_if_called(command, capture_output, text):
        raise AssertionError("analyzer subprocess should not run")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fail_if_called)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "invalid-inputs"
    assert any("PB3/PB2" in failure for failure in report["failures"])


def test_run_rejects_invalid_attenuation_summary_contract(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_attenuation_fixture(root)
    (root / "results/20260808-e0-05-step-01-30db.json").write_text(
        json.dumps({"requested_packets": 200}) + "\n",
        encoding="utf-8",
    )

    def fail_if_called(command, capture_output, text):
        raise AssertionError("analyzer subprocess should not run")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fail_if_called)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "invalid-inputs"
    assert any("transmitted_packets is required" in failure for failure in report["failures"])
    assert any("rx_count is required" in failure for failure in report["failures"])


def test_run_rejects_undersized_attenuation_summary_contract(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_attenuation_fixture(root)
    (root / "results/20260808-e0-05-step-01-30db.json").write_text(
        json.dumps(
            {
                "requested_packets": 50,
                "transmitted_packets": 50,
                "rx_count": 25,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_if_called(command, capture_output, text):
        raise AssertionError("analyzer subprocess should not run")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fail_if_called)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "invalid-inputs"
    assert any("requested_packets 50 below required 200" in failure for failure in report["failures"])
    assert any("transmitted_packets 50 below required 200" in failure for failure in report["failures"])


def test_run_rejects_invalid_audio_csv_contract(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)
    (root / "results/20260808-e0-07-audio.csv").write_text(
        "time_us,frame_id\n0,1\n",
        encoding="utf-8",
    )

    def fail_if_called(command, capture_output, text):
        raise AssertionError("analyzer subprocess should not run")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fail_if_called)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "invalid-inputs"
    assert any("event column" in failure for failure in report["failures"])


def test_run_fails_when_summary_json_missing(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)

    def fake_run(command, capture_output, text):
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fake_run)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "failed"
    assert report["returncode"] == 0
    assert any("summary JSON missing" in item for item in report["failures"])


def test_run_fails_when_summary_json_invalid(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)
    summary_path = root / "results/20260808-e0-07-audio.summary.json"

    def fake_run(command, capture_output, text):
        summary_path.write_text("{not json\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fake_run)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "failed"
    assert "summary JSON is invalid" in report["failures"]


def test_run_fails_when_summary_json_reports_failure(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)
    summary_path = root / "results/20260808-e0-07-audio.summary.json"

    def fake_run(command, capture_output, text):
        summary_path.write_text(
            json.dumps({"pass": False, "complete_samples": 0}) + "\n",
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr("run_prototype0_fixture_analysis.subprocess.run", fake_run)

    report = run(readiness, root=root)

    assert report["pass"] is False
    assert report["status"] == "failed"
    assert report["summary"]["pass"] is False
    assert "summary JSON did not report pass:true" in report["failures"]


def test_cli_dry_run_outputs_command(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--readiness",
            str(readiness),
            "--root",
            str(root),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    report = json.loads(result.stdout)
    assert report["status"] == "dry-run"
    assert report["analysis_command"][1] == "tools/analyze_audio_loopback.py"


def test_cli_dry_run_allows_missing_inputs(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_audio_fixture(root)
    (root / "results/20260808-e0-07-audio.csv").unlink()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--readiness",
            str(readiness),
            "--root",
            str(root),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    report = json.loads(result.stdout)
    assert report["status"] == "dry-run"
    assert report["inputs"][0]["exists"] is False


def test_discover_readiness_ignores_templates_and_examples(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    results = root / "results"
    results.mkdir(parents=True)
    (results / "20260808-e0-03-readiness-template.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    (results / "20260808-e0-03-ready-example.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    readiness = _write_ready_gpio_fixture(root)

    assert discover_readiness(root, "E0-03") == readiness


def test_cli_gate_discovery_dry_run(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    readiness = _write_ready_gpio_fixture(root)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-03",
            "--root",
            str(root),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    report = json.loads(result.stdout)
    assert report["status"] == "dry-run"
    assert report["readiness"] == str(readiness)
    assert report["analysis_command"][1] == "tools/analyze_scheduled_tx_gpio.py"


def test_cli_gate_discovery_reports_missing_live_readiness(tmp_path: Path) -> None:
    root = tmp_path / "fg23"
    results = root / "results"
    results.mkdir(parents=True)
    (results / "20260808-e0-07-readiness-template.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-07",
            "--root",
            str(root),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    report = json.loads(result.stdout)
    assert result.returncode == 1
    assert report["status"] == "no-readiness"
    assert report["schema"] == "prototype0-fixture-run-report-v1"
    assert report["generated_at"]
    assert report["root"] == str(root)
    assert "no live readiness file found" in report["failures"][0]
