import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1]))

from analyze_audio_loopback import analyze_audio_loopback


SCRIPT = Path(__file__).parents[1] / "analyze_audio_loopback.py"


def test_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "audio loopback timing captures" in result.stdout


def test_analyze_audio_loopback_event_chain(tmp_path: Path) -> None:
    capture = tmp_path / "audio.csv"
    capture.write_text(
        "\n".join(
            [
                "frame_id,event,time_us",
                "1,impulse,0",
                "1,capture_frame,10000",
                "1,packet_queue,30000",
                "1,tx_start,35000",
                "1,rx_done,60000",
                "1,playback_output,90000",
                "2,impulse,100000",
                "2,capture_frame,110000",
                "2,packet_queue,130000",
                "2,tx_start,135000",
                "2,rx_done,160000",
                "2,playback_output,190000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_audio_loopback(capture, expected_samples=2)

    assert summary["complete_samples"] == 2
    assert summary["pass"] is True
    assert summary["capture_latency"]["max_us"] == 10000
    assert summary["end_to_end_latency"]["max_us"] == 90000


def test_fails_when_latency_exceeds_target(tmp_path: Path) -> None:
    capture = tmp_path / "audio.csv"
    capture.write_text(
        "\n".join(
            [
                "frame_id,event,time_us",
                "1,impulse,0",
                "1,capture_frame,10000",
                "1,packet_queue,30000",
                "1,tx_start,35000",
                "1,rx_done,60000",
                "1,playback_output,200000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_audio_loopback(capture, expected_samples=1)

    assert summary["complete_samples"] == 1
    assert summary["pass"] is False
    assert summary["end_to_end_latency"]["max_us"] == 200000


def test_reports_missing_frames(tmp_path: Path) -> None:
    capture = tmp_path / "audio.csv"
    capture.write_text(
        "\n".join(
            [
                "sequence,marker,Time [s]",
                "1,impulse,0.000",
                "1,capture_frame,0.010",
                "1,packet_queue,0.030",
                "1,tx_start,0.035",
                "1,rx_done,0.060",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_audio_loopback(capture, expected_samples=1)

    assert summary["complete_samples"] == 0
    assert summary["incomplete_samples"] == 1
    assert summary["missing_frames"][0]["missing_events"] == ["playback_output"]


def test_rejects_non_monotonic_event_chain(tmp_path: Path) -> None:
    capture = tmp_path / "audio.csv"
    capture.write_text(
        "\n".join(
            [
                "frame_id,event,time_us",
                "1,impulse,0",
                "1,capture_frame,10000",
                "1,packet_queue,30000",
                "1,tx_start,35000",
                "1,rx_done,60000",
                "1,playback_output,50000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_audio_loopback(capture, expected_samples=1)

    assert summary["complete_samples"] == 0
    assert summary["invalid_samples"] == 1
    assert summary["invalid_frames"][0]["negative_stages"] == ["playback_latency_us"]
    assert summary["pass"] is False


def test_event_name_overrides(tmp_path: Path) -> None:
    capture = tmp_path / "audio.csv"
    capture.write_text(
        "\n".join(
            [
                "id,event,time_us",
                "1,audio_in,0",
                "1,frame_ready,10000",
                "1,queued,30000",
                "1,radio_start,35000",
                "1,radio_rx,60000",
                "1,audio_out,90000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = analyze_audio_loopback(
        capture,
        expected_samples=1,
        events={
            "impulse": "audio_in",
            "capture": "frame_ready",
            "queue": "queued",
            "tx_start": "radio_start",
            "rx": "radio_rx",
            "playback": "audio_out",
        },
    )

    assert summary["complete_samples"] == 1
    assert summary["pass"] is True
