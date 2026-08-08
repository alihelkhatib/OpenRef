import subprocess
import sys
from pathlib import Path

from openref_memory_watermark_probe import parse_mem_markers


SCRIPT = Path(__file__).parents[1] / "openref_memory_watermark_probe.py"


def test_memory_watermark_probe_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "fixed memory footprint" in result.stdout


def test_parse_mem_markers() -> None:
    text = "{{(openrefMem)}{StateBytes:16}{MaxPacketBytes:273}{Rx:50}{Gaps:0}{Faults:0}}}"

    assert parse_mem_markers(text) == [
        {
            "state_bytes": 16,
            "max_packet_bytes": 273,
            "rx": 50,
            "gaps": 0,
            "faults": 0,
        }
    ]
