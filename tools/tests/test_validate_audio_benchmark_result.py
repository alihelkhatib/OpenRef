import json
from pathlib import Path

from validate_audio_benchmark_result import validate_artifact_files, validate_result


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "firmware/audio_processor/targets/mimxrt595_evk/benchmark-result-template.json"


def template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def passing_result() -> dict:
    data = template()
    data.update({
        "clock_hz": 200000000,
        "completed_blocks": 180000,
        "plc_calls": 100,
        "maximum_total_us": 7000,
        "stack_high_water_bytes": 4096,
        "stack_reserved_bytes": 8192,
        "static_memory_bytes": 200000,
        "memory_capacity_bytes": 5242880,
        "idle_current_ma": 10.0,
        "one_talker_current_ma": 20.0,
        "six_talker_current_ma": 30.0,
        "complete": True,
        "passed": True,
        "artifact_sha256": {
            "serial_log": "1" * 64,
            "elf": "2" * 64,
            "map": "3" * 64,
        },
    })
    return data


def test_template_is_valid_incomplete_evidence() -> None:
    assert validate_result(template()) == []
    assert validate_result(template(), require_promotion=True)


def test_complete_measured_result_is_promotion_ready() -> None:
    assert validate_result(passing_result(), require_promotion=True) == []


def test_false_pass_and_missing_current_are_rejected() -> None:
    data = passing_result()
    data["maximum_total_us"] = 8001
    assert any("passed" in error for error in validate_result(data))
    data = passing_result()
    data["idle_current_ma"] = None
    errors = validate_result(data, require_promotion=True)
    assert any("idle_current_ma" in error for error in errors)


def test_compute_only_io_and_memory_margin_are_rejected() -> None:
    data = passing_result()
    data["audio_io_mode"] = "compute-only"
    assert any("passed" in error for error in validate_result(data))
    data = passing_result()
    data["stack_high_water_bytes"] = 7000
    assert any("stack high-water" in error for error in validate_result(data, True))


def test_dma_fault_and_missing_artifact_evidence_are_rejected() -> None:
    data = passing_result()
    data["capture_dma_overruns"] = 1
    assert any("passed" in error for error in validate_result(data))
    data = passing_result()
    data["artifact_sha256"]["elf"] = "not-a-hash"
    assert any("SHA-256" in error for error in validate_result(data, True))


def test_artifact_bytes_are_verified_and_tampering_is_rejected(tmp_path: Path) -> None:
    import hashlib

    data = passing_result()
    contents = {"serial_log": b"serial", "elf": b"elf", "map": b"map"}
    for key, content in contents.items():
        path = tmp_path / data["artifact_files"][key]
        path.write_bytes(content)
        data["artifact_sha256"][key] = hashlib.sha256(content).hexdigest()
    assert validate_artifact_files(data, tmp_path) == []
    (tmp_path / data["artifact_files"]["elf"]).write_bytes(b"tampered")
    assert any("hash mismatch: elf" in error for error in validate_artifact_files(data, tmp_path))


def test_artifact_path_escape_is_rejected() -> None:
    data = passing_result()
    data["artifact_files"]["map"] = "../outside.map"
    assert any("safe relative filenames" in error for error in validate_result(data, True))
