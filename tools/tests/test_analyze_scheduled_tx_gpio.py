import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from analyze_scheduled_tx_gpio import analyze_gpio_csv, pair_edge_report, pair_edges


SCRIPT = Path(__file__).parents[1] / "analyze_scheduled_tx_gpio.py"


def test_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "scheduled-TX GPIO marker captures" in result.stdout


def test_pair_edges_uses_next_start_after_queue() -> None:
    errors = pair_edges([100.0, 200.0, 300.0], [90.0, 104.0, 205.0, 303.0])

    assert errors == [4.0, 5.0, 3.0]


def test_pair_edge_report_counts_unpaired_edges() -> None:
    report = pair_edge_report(
        [100.0, 200.0, 300.0],
        [90.0, 104.0, 205.0, 400.0],
    )

    assert report["launch_errors_us"] == [4.0, 5.0, 100.0]
    assert report["orphan_start_edges"] == 1
    assert report["unpaired_queue_edges"] == 0
    assert report["extra_start_edges"] == 0


def test_analyze_edge_list_csv(tmp_path: Path) -> None:
    capture = tmp_path / "edges.csv"
    capture.write_text(
        "\n".join(
            [
                "Time [s],Channel,Value",
                "0.000100,PB3,1",
                "0.000101,PB3,0",
                "0.000104,PB2,1",
                "0.000105,PB2,0",
                "0.000200,PB3,1",
                "0.000201,PB3,0",
                "0.000204,PB2,1",
                "0.000205,PB2,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_gpio_csv(
        capture,
        queue_channel="PB3",
        start_channel="PB2",
        expected_samples=2,
    )

    assert summary["csv_shape"] == "edge-list"
    assert summary["paired_samples"] == 2
    assert summary["launch_error_min_us"] == 4.0
    assert summary["launch_error_max_us"] == 4.0
    assert summary["pass"] is True


def test_analyze_sampled_columns_csv(tmp_path: Path) -> None:
    capture = tmp_path / "sampled.csv"
    capture.write_text(
        "\n".join(
            [
                "time_s,PB3,PB2",
                "0.000100,0,0",
                "0.000101,1,0",
                "0.000102,0,0",
                "0.000106,0,1",
                "0.000107,0,0",
                "0.000200,1,0",
                "0.000201,0,0",
                "0.000205,0,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_gpio_csv(
        capture,
        queue_channel="PB3",
        start_channel="PB2",
        expected_samples=2,
        max_launch_error_us=6,
    )

    assert summary["csv_shape"] == "sampled-columns"
    assert summary["queue_edges"] == 2
    assert summary["start_edges"] == 2
    assert summary["launch_error_max_us"] == 5.0
    assert summary["pass"] is True


def test_fails_when_too_few_samples(tmp_path: Path) -> None:
    capture = tmp_path / "edges.csv"
    capture.write_text("time_s,channel\n0.000100,PB3\n0.000104,PB2\n", encoding="utf-8")

    summary = analyze_gpio_csv(
        capture,
        queue_channel="PB3",
        start_channel="PB2",
        expected_samples=2,
    )

    assert summary["paired_samples"] == 1
    assert summary["pass"] is False


def test_reports_unpaired_edges_without_failing_by_default(tmp_path: Path) -> None:
    capture = tmp_path / "edges.csv"
    capture.write_text(
        "\n".join(
            [
                "Time [s],Channel,Value",
                "0.000090,PB2,1",
                "0.000091,PB2,0",
                "0.000100,PB3,1",
                "0.000101,PB3,0",
                "0.000104,PB2,1",
                "0.000105,PB2,0",
                "0.000200,PB3,1",
                "0.000201,PB3,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_gpio_csv(
        capture,
        queue_channel="PB3",
        start_channel="PB2",
        expected_samples=1,
    )

    assert summary["paired_samples"] == 1
    assert summary["orphan_start_edges"] == 1
    assert summary["unpaired_queue_edges"] == 1
    assert summary["pass"] is True


def test_strict_mode_fails_on_unpaired_edges(tmp_path: Path) -> None:
    capture = tmp_path / "edges.csv"
    capture.write_text(
        "\n".join(
            [
                "Time [s],Channel,Value",
                "0.000100,PB3,1",
                "0.000101,PB3,0",
                "0.000104,PB2,1",
                "0.000105,PB2,0",
                "0.000200,PB3,1",
                "0.000201,PB3,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_gpio_csv(
        capture,
        queue_channel="PB3",
        start_channel="PB2",
        expected_samples=1,
        fail_on_unpaired_edges=True,
    )

    assert summary["paired_samples"] == 1
    assert summary["unpaired_queue_edges"] == 1
    assert summary["pass"] is False
