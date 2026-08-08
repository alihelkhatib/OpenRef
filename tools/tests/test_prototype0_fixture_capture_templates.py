import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from analyze_attenuation_sweep import analyze
from analyze_audio_loopback import analyze_audio_loopback
from analyze_scheduled_tx_gpio import analyze_gpio_csv
from prototype0_fixture_capture_templates import (
    SUPPORTED_GATES,
    gates_from_arg,
    write_capture_templates,
)


SCRIPT = Path(__file__).parents[1] / "prototype0_fixture_capture_templates.py"


def test_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "capture-file templates" in result.stdout


def test_gates_from_arg_expands_all() -> None:
    assert gates_from_arg("all") == SUPPORTED_GATES
    assert gates_from_arg("E0-05") == ("E0-05",)


def test_write_all_capture_templates_without_force(tmp_path: Path) -> None:
    first = write_capture_templates(SUPPORTED_GATES, tmp_path)
    second = write_capture_templates(SUPPORTED_GATES, tmp_path)

    assert len(first) == 4
    assert all(item["written"] is True for item in first)
    assert all(Path(item["path"]).exists() for item in first)
    assert all(item["written"] is False for item in second)
    assert all(item["reason"] == "exists" for item in second)


def test_capture_templates_are_written_with_lf_bytes(tmp_path: Path) -> None:
    written = write_capture_templates(SUPPORTED_GATES, tmp_path)

    for item in written:
        raw = Path(item["path"]).read_bytes()
        assert b"\r\n" not in raw
        assert item["bytes"] == len(raw)


def test_e0_03_template_is_shape_valid_but_not_passing_evidence(tmp_path: Path) -> None:
    write_capture_templates(("E0-03",), tmp_path)
    summary = analyze_gpio_csv(
        tmp_path / "e0-03-scheduled-tx-gpio-template.csv",
        queue_channel="PB3",
        start_channel="PB2",
        expected_samples=100,
        fail_on_unpaired_edges=True,
    )

    assert summary["csv_shape"] == "edge-list"
    assert summary["paired_samples"] == 2
    assert summary["pass"] is False


def test_e0_05_templates_require_measured_packet_counts(tmp_path: Path) -> None:
    write_capture_templates(("E0-05",), tmp_path)
    summary = analyze(
        [
            tmp_path / "e0-05-step-00-baseline-template.json",
            tmp_path / "e0-05-step-01-30db-template.json",
        ],
        labels=["baseline", "30dB"],
    )

    assert summary["valid_steps"] == 0
    assert summary["pass"] is False


def test_e0_07_template_is_shape_valid_but_not_passing_evidence(tmp_path: Path) -> None:
    write_capture_templates(("E0-07",), tmp_path)
    summary = analyze_audio_loopback(
        tmp_path / "e0-07-audio-loopback-template.csv",
        expected_samples=10,
    )

    assert summary["complete_samples"] == 1
    assert summary["pass"] is False


def test_cli_writes_json_manifest(tmp_path: Path) -> None:
    output_dir = tmp_path / "templates"
    manifest = tmp_path / "manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            "E0-03",
            "--output-dir",
            str(output_dir),
            "--json",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert '"pass": true' in result.stdout
    assert manifest.exists()
    assert (output_dir / "e0-03-scheduled-tx-gpio-template.csv").exists()
