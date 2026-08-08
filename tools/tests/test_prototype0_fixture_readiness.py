import json
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from prototype0_fixture_readiness import (
    READINESS_SCHEMA,
    analysis_command,
    apply_audio_events,
    apply_attenuated_steps,
    apply_set,
    command_text,
    template,
    validate,
)


SCRIPT = Path(__file__).parents[1] / "prototype0_fixture_readiness.py"


def test_e0_03_template_contains_strict_gpio_flags() -> None:
    data = template("E0-03")

    assert data["schema"] == READINESS_SCHEMA
    assert data["channels"] == {"queue": "PB3", "start": "PB2"}
    assert "--fail-on-unpaired-edges" in data["analyzer_flags"]


def test_validate_requires_readiness_schema() -> None:
    data = template("E0-03")
    data.pop("schema")

    failures = validate("E0-03", data)

    assert f"schema must be {READINESS_SCHEMA}" in failures


def test_validate_e0_05_ready_metadata() -> None:
    data = template("E0-05")
    data.update(
        {
            "method": "Mini-Circuits VAT-30+ inline attenuator",
            "baseline_summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
            "physical_setup_note": "COM10 SMA cabled through 30 dB attenuator to shielded receive setup.",
        }
    )
    data["attenuated_steps"] = [
        {
            "label": "30 dB",
            "physical_setting": "30 dB inline attenuator",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
        }
    ]

    assert validate("E0-05", data) == []


def test_analysis_command_for_e0_05_ready_metadata() -> None:
    data = template("E0-05")
    data.update(
        {
            "method": "Mini-Circuits VAT-30+ inline attenuator",
            "baseline_summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
            "physical_setup_note": "COM10 SMA cabled through 30 dB attenuator to shielded receive setup.",
        }
    )
    data["attenuated_steps"] = [
        {
            "label": "30dB",
            "physical_setting": "30 dB inline attenuator",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
        }
    ]

    command = analysis_command("E0-05", data)

    assert command[:2] == ["python", "tools/analyze_attenuation_sweep.py"]
    assert all("\\" not in item for item in command)
    assert "--labels" in command
    assert "baseline" in command
    assert "30dB" in command
    assert "firmware/prototype0/fg23/results/20260808-e0-05-attenuation-summary.json" in command
    assert not any("YYYYMMDD" in item for item in command)


def test_validate_e0_05_template_placeholders_fail() -> None:
    data = template("E0-05")

    failures = validate("E0-05", data)

    assert "physical_setup_note is required" in failures
    assert "attenuated_steps[0].physical_setting is required" in failures
    assert "attenuated_steps[0].summary_json must be a filled .json path" in failures


def test_validate_e0_03_requires_csv_output() -> None:
    data = template("E0-03")
    data.update(
        {
            "instrument": "Saleae Logic Pro 8",
            "ground_connected": True,
            "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-summary.json",
        }
    )

    failures = validate("E0-03", data)

    assert "output_csv must be a filled .csv path" in failures


def test_analysis_command_for_e0_03_ready_metadata() -> None:
    data = template("E0-03")
    data.update(
        {
            "instrument": "Saleae Logic Pro 8",
            "ground_connected": True,
            "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv",
        }
    )

    command = analysis_command("E0-03", data)

    assert command[:2] == ["python", "tools/analyze_scheduled_tx_gpio.py"]
    assert all("\\" not in item for item in command)
    assert "--queue-channel" in command
    assert "PB3" in command
    assert "--fail-on-unpaired-edges" in command


def test_validate_e0_03_requires_flag_list() -> None:
    data = template("E0-03")
    data.update(
        {
            "instrument": "Saleae Logic Pro 8",
            "ground_connected": True,
            "output_csv": "firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv",
            "analyzer_flags": "--fail-on-unpaired-edges",
        }
    )

    failures = validate("E0-03", data)

    assert "analyzer_flags must be a list of strings" in failures


def test_validate_e0_05_requires_json_summaries() -> None:
    data = template("E0-05")
    data.update(
        {
            "method": "Mini-Circuits VAT-30+ inline attenuator",
            "baseline_summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-baseline.csv",
            "physical_setup_note": "COM10 SMA cabled through 30 dB attenuator to shielded receive setup.",
        }
    )
    data["attenuated_steps"] = [
        {
            "label": "30 dB",
            "physical_setting": "30 dB inline attenuator",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-01.csv",
        }
    ]

    failures = validate("E0-05", data)

    assert "baseline_summary_json must be a filled .json path" in failures
    assert "attenuated_steps[0].summary_json must be a filled .json path" in failures


def test_validate_e0_05_requires_unique_filled_labels() -> None:
    data = template("E0-05")
    data.update(
        {
            "method": "Mini-Circuits VAT-30+ inline attenuator",
            "baseline_summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-baseline.json",
            "physical_setup_note": "COM10 SMA cabled through attenuator to shielded receive setup.",
        }
    )
    data["attenuated_steps"] = [
        {
            "label": "30dB",
            "physical_setting": "30 dB inline attenuator",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-01.json",
        },
        {
            "label": "30dB",
            "physical_setting": "60 dB inline attenuator",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-02.json",
        },
        {
            "label": "",
            "physical_setting": "90 dB inline attenuator",
            "summary_json": "firmware/prototype0/fg23/results/20260808-e0-05-step-03.json",
        },
    ]

    failures = validate("E0-05", data)

    assert "attenuated_steps labels must be unique" in failures
    assert "attenuated_steps[2].label is required" in failures


def test_validate_e0_07_reports_missing_fixture_fields() -> None:
    data = template("E0-07")

    failures = validate("E0-07", data)

    assert "firmware_timing_markers must be true" in failures


def test_validate_e0_07_rejects_duplicate_or_unexpected_events() -> None:
    data = template("E0-07")
    data.update(
        {
            "fixture_method": "wired DAC output into ADC capture fixture",
            "firmware_timing_markers": True,
            "output_csv": "firmware/prototype0/fg23/results/20260808-e0-07-audio.csv",
        }
    )
    data["events"] = data["events"] + ["impulse", "debug_probe"]

    failures = validate("E0-07", data)

    assert "events must not contain duplicates" in failures
    assert "events unexpected: debug_probe" in failures


def test_e0_07_template_contains_event_aliases() -> None:
    data = template("E0-07")

    assert data["event_aliases"]["capture"] == "capture_frame"
    assert set(data["events"]) == set(data["event_aliases"].values())


def test_apply_audio_events_updates_events_and_aliases() -> None:
    data = template("E0-07")

    apply_audio_events(data, ["capture=frame_ready", "playback=audio_out"])

    assert data["event_aliases"]["capture"] == "frame_ready"
    assert data["event_aliases"]["playback"] == "audio_out"
    assert "frame_ready" in data["events"]
    assert "capture_frame" not in data["events"]


def test_apply_audio_events_rejects_unknown_key() -> None:
    data = template("E0-07")

    try:
        apply_audio_events(data, ["unknown=marker"])
    except ValueError as exc:
        assert "unsupported audio event key unknown" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_validate_e0_07_rejects_mismatched_alias_events() -> None:
    data = template("E0-07")
    data.update(
        {
            "fixture_method": "wired DAC output into ADC capture fixture",
            "firmware_timing_markers": True,
            "output_csv": "firmware/prototype0/fg23/results/20260808-e0-07-audio.csv",
        }
    )
    data["event_aliases"]["playback"] = "audio_out"

    failures = validate("E0-07", data)

    assert "events missing: audio_out" in failures
    assert "events unexpected: playback_output" in failures


def test_command_text_quotes_spaces_for_powershell() -> None:
    command = ["python", "tools/analyze_audio_loopback.py", "path with spaces/capture.csv"]

    assert command_text(command) == "python tools/analyze_audio_loopback.py 'path with spaces/capture.csv'"


def test_apply_set_updates_nested_template_values() -> None:
    data = template("E0-05")

    apply_set(data, "packet_count_per_step=250")
    apply_set(data, "same_direction_all_steps=true")
    apply_set(data, "attenuated_steps.0.label=30dB")
    apply_set(data, "attenuated_steps.0.summary_json=firmware/prototype0/fg23/results/step.json")

    assert data["packet_count_per_step"] == 250
    assert data["same_direction_all_steps"] is True
    assert data["attenuated_steps"][0]["label"] == "30dB"
    assert data["attenuated_steps"][0]["summary_json"].endswith("step.json")


def test_apply_set_rejects_unknown_path() -> None:
    data = template("E0-03")

    try:
        apply_set(data, "channels.done=PA5")
    except ValueError as exc:
        assert "unknown assignment path" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_apply_attenuated_steps_replaces_template_steps() -> None:
    data = template("E0-05")

    apply_attenuated_steps(
        data,
        [
            "label=30dB,physical_setting=30 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/step-01.json",
            "label=60dB,physical_setting=60 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/step-02.json",
        ],
    )

    assert [step["label"] for step in data["attenuated_steps"]] == ["30dB", "60dB"]
    assert data["attenuated_steps"][1]["physical_setting"] == "60 dB inline attenuator"


def test_apply_attenuated_steps_rejects_incomplete_step() -> None:
    data = template("E0-05")

    try:
        apply_attenuated_steps(data, ["label=30dB,summary_json=firmware/prototype0/fg23/results/step.json"])
    except ValueError as exc:
        assert "attenuated step missing: physical_setting" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_cli_check_fails_for_incomplete_e0_03(tmp_path: Path) -> None:
    check = tmp_path / "readiness.json"
    data = template("E0-03")
    data["ground_connected"] = False
    check.write_text(json.dumps(data) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--gate", "E0-03", "--check", str(check)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "ground_connected must be true" in result.stdout


def test_cli_template_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--gate", "E0-05", "--template"],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert data["gate"] == "E0-05"
    assert data["schema"] == READINESS_SCHEMA


def test_cli_fill_outputs_ready_metadata(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-03",
            "--fill",
            "--set",
            "instrument=Saleae Logic Pro 8",
            "--set",
            "ground_connected=true",
            "--set",
            "output_csv=firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv",
            "--json",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert data["gate"] == "E0-03"
    assert data["schema"] == READINESS_SCHEMA
    assert "pass" not in data
    assert written["instrument"] == "Saleae Logic Pro 8"
    assert written["schema"] == READINESS_SCHEMA
    assert validate("E0-03", written) == []


def test_cli_fill_fails_when_metadata_is_not_ready(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-07",
            "--fill",
            "--json",
            str(output),
        ],
        capture_output=True,
        text=True,
    )

    data = json.loads(result.stdout)
    assert result.returncode == 1
    assert data["pass"] is False
    assert "metadata" in data
    assert "firmware_timing_markers must be true" in data["failures"]


def test_cli_fill_outputs_ready_e0_05_metadata_with_steps(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-05",
            "--fill",
            "--set",
            "method=Mini-Circuits VAT-30+ inline attenuator",
            "--set",
            "baseline_summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json",
            "--set",
            "physical_setup_note=COM10 SMA cabled through attenuator to shielded receive setup.",
            "--attenuated-step",
            "label=30dB,physical_setting=30 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json",
            "--attenuated-step",
            "label=60dB,physical_setting=60 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-02-60db.json",
            "--json",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    assert validate("E0-05", data) == []
    command = analysis_command("E0-05", data)
    assert command is not None
    assert "30dB" in command
    assert "60dB" in command
    assert json.loads(output.read_text(encoding="utf-8"))["attenuated_steps"][1]["label"] == "60dB"


def test_cli_check_includes_analysis_command_for_ready_file(tmp_path: Path) -> None:
    check = tmp_path / "readiness.json"
    data = template("E0-07")
    data.update(
        {
            "fixture_method": "wired DAC output into ADC capture fixture",
            "firmware_timing_markers": True,
            "output_csv": "firmware/prototype0/fg23/results/20260808-e0-07-audio.csv",
        }
    )
    check.write_text(json.dumps(data) + "\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--gate", "E0-07", "--check", str(check)],
        capture_output=True,
        text=True,
        check=True,
    )

    output = json.loads(result.stdout)
    assert output["pass"] is True
    assert output["analysis_command"][:2] == ["python", "tools/analyze_audio_loopback.py"]
    assert output["analysis_command_text"].startswith("python tools/analyze_audio_loopback.py ")
    assert all("\\" not in item for item in output["analysis_command"])


def test_cli_fill_outputs_ready_e0_07_metadata_with_event_aliases(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-07",
            "--fill",
            "--set",
            "fixture_method=wired DAC output into ADC capture fixture",
            "--set",
            "firmware_timing_markers=true",
            "--set",
            "output_csv=firmware/prototype0/fg23/results/20260808-e0-07-audio.csv",
            "--audio-event",
            "capture=frame_ready",
            "--audio-event",
            "playback=audio_out",
            "--json",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    command = analysis_command("E0-07", data)
    assert validate("E0-07", data) == []
    assert command is not None
    assert "--event" in command
    assert "capture=frame_ready" in command
    assert "playback=audio_out" in command
    assert json.loads(output.read_text(encoding="utf-8"))["event_aliases"]["playback"] == "audio_out"
