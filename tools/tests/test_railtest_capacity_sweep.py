import json
import subprocess
import sys
from pathlib import Path

import importlib.util


SCRIPT = Path(__file__).parents[1] / "railtest_capacity_sweep.py"
TOOLS_DIR = SCRIPT.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
SPEC = importlib.util.spec_from_file_location("railtest_capacity_sweep", SCRIPT)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_capacity_sweep_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Run a small RAILtest payload sweep" in result.stdout


def test_run_sweep_aggregates_each_payload(tmp_path: Path, monkeypatch) -> None:
    calls = []

    def fake_run_packet_check(**kwargs):
        calls.append(kwargs)
        kwargs["summary_json"].write_text(
            json.dumps({"payload_bytes": kwargs["payload_bytes"], "pass": True}),
            encoding="utf-8",
        )
        return 0

    monkeypatch.setattr(MODULE, "run_packet_check", fake_run_packet_check)
    monkeypatch.setattr(MODULE, "datetime", _FixedDatetime)

    result = MODULE.run_sweep(
        rx_port="COM8",
        tx_port="COM10",
        payloads=[16, 60],
        packets=25,
        tx_delay_ms=7,
        settle_seconds=1.5,
        rf_path=1,
        output_dir=tmp_path,
    )

    assert result == 0
    assert [call["payload_bytes"] for call in calls] == [16, 60]
    assert all(call["rx_port"] == "COM8" for call in calls)
    assert all(call["tx_port"] == "COM10" for call in calls)
    assert all(call["packets"] == 25 for call in calls)
    assert all(call["tx_delay_ms"] == 7 for call in calls)
    assert all(call["settle_seconds"] == 1.5 for call in calls)
    assert all(call["rf_path"] == 1 for call in calls)
    aggregate = tmp_path / "20260812-railtest-capacity-sweep-summary.json"
    assert json.loads(aggregate.read_text(encoding="utf-8")) == [
        {"pass": True, "payload_bytes": 16},
        {"pass": True, "payload_bytes": 60},
    ]


def test_run_sweep_continues_and_fails_if_any_payload_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempted = []

    def fake_run_packet_check(**kwargs):
        payload = kwargs["payload_bytes"]
        attempted.append(payload)
        kwargs["summary_json"].write_text(
            json.dumps({"payload_bytes": payload}),
            encoding="utf-8",
        )
        return 1 if payload == 60 else 0

    monkeypatch.setattr(MODULE, "run_packet_check", fake_run_packet_check)
    monkeypatch.setattr(MODULE, "datetime", _FixedDatetime)

    result = MODULE.run_sweep(
        rx_port="COM8",
        tx_port="COM10",
        payloads=[16, 60, 120],
        packets=10,
        tx_delay_ms=20,
        settle_seconds=2,
        rf_path=0,
        output_dir=tmp_path,
    )

    assert result == 1
    assert attempted == [16, 60, 120]
    aggregate = tmp_path / "20260812-railtest-capacity-sweep-summary.json"
    assert [item["payload_bytes"] for item in json.loads(aggregate.read_text())] == [
        16,
        60,
        120,
    ]


class _FixedDatetime:
    @staticmethod
    def now():
        return _FixedNow()


class _FixedNow:
    @staticmethod
    def strftime(_format: str) -> str:
        return "20260812"
