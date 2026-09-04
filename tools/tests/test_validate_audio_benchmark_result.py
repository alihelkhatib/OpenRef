import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate_audio_benchmark_result.py"
SPEC = importlib.util.spec_from_file_location("audio_result_validator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def passing_result() -> dict:
    result = dict(MODULE.EXPECTED)
    result.update({
        "target": "board-rev-a",
        "silicon_revision": "A1",
        "clock_hz": 200_000_000,
        "compiler": "vendor cc 1.0",
        "optimization": "-O3",
        "codec": "LC3 1.2.3",
        "firmware_commit": "0123456789abcdef",
        "memory_placement": "code/data in internal SRAM",
        "clock_configuration": "core 200 MHz, buses 100 MHz, SRAM 100 MHz",
        "timer_source": "32-bit 1 MHz GPT derived from 24 MHz oscillator",
        "current_measurement": "board 5 V input, Joulescope JS220, 10 kHz, radios disabled",
        "completed_blocks": 180000,
        "plc_calls": 927,
        "encode_failures": 0,
        "decode_failures": 0,
        "process_failures": 0,
        "deadline_misses": 0,
        "maximum_encode_us": 1000,
        "maximum_render_us": 5000,
        "maximum_total_us": 6000,
        "average_encode_us": 800,
        "average_render_us": 4000,
        "average_total_us": 4800,
        "stack_high_water_bytes": 4096,
        "pacing_ticks": 181000,
        "pacing_overruns": 0,
        "elapsed_us": 1_810_006_000,
        "idle_current_ma": 5.1,
        "one_talker_current_ma": 9.2,
        "six_talker_current_ma": 15.3,
        "complete": True,
        "passed": True,
    })
    return result


def test_accepts_complete_fixed_workload() -> None:
    assert MODULE.validate_result(passing_result()) == []


def test_rejects_self_reported_pass_with_wrong_workload() -> None:
    result = passing_result()
    result["decoder_count"] = 4
    result["plc_period_packets"] = 96
    result["maximum_total_us"] = 8001
    errors = MODULE.validate_result(result)
    assert "decoder_count must equal 5" in errors
    assert "plc_period_packets must equal 97" in errors
    assert "maximum_total_us must be at most 8000" in errors


def test_rejects_missing_power_evidence() -> None:
    result = passing_result()
    result["six_talker_current_ma"] = None
    assert "six_talker_current_ma must be a positive finite measurement" in MODULE.validate_result(result)


def test_rejects_boolean_counts_and_inconsistent_timing() -> None:
    result = passing_result()
    result["plc_calls"] = True
    result["average_total_us"] = 4700
    result["maximum_encode_us"] = 7000
    errors = MODULE.validate_result(result)
    assert "plc_calls must be a non-negative integer" in errors
    assert any(error.startswith("average_total_us must be the sum") for error in errors)
    assert "maximum_total_us must cover encode and render maxima" in errors


def test_rejects_type_confused_fixed_workload_fields() -> None:
    result = passing_result()
    result["benchmark_version"] = True
    result["sample_rate_hz"] = 16000.0
    errors = MODULE.validate_result(result)
    assert "benchmark_version must equal 1" in errors
    assert "sample_rate_hz must equal 16000" in errors


def test_rejects_wrong_deterministic_plc_count() -> None:
    assert MODULE.expected_plc_calls() == 927
    result = passing_result()
    result["plc_calls"] = 926
    assert "plc_calls must equal 927" in MODULE.validate_result(result)


def test_accepts_one_microsecond_average_truncation() -> None:
    result = passing_result()
    result["average_total_us"] = 4801
    assert MODULE.validate_result(result) == []


def test_rejects_placeholder_evidence_and_missing_measurement_provenance() -> None:
    result = passing_result()
    result["maximum_total_us"] = 0
    result["stack_high_water_bytes"] = 0
    result["timer_source"] = ""
    result.pop("current_measurement")
    errors = MODULE.validate_result(result)
    assert "maximum_total_us must be positive" in errors
    assert "stack_high_water_bytes must be positive" in errors
    assert "timer_source must be a non-empty string" in errors
    assert "current_measurement must be a non-empty string" in errors


def test_rejects_unpaced_or_wrong_duration_capture() -> None:
    result = passing_result()
    result["pacing_ticks"] = 180999
    result["pacing_overruns"] = 1
    result["elapsed_us"] = 1_809_999_999
    errors = MODULE.validate_result(result)
    assert "pacing_ticks must equal 181000" in errors
    assert "pacing_overruns must equal 0" in errors
    assert any(error.startswith("elapsed_us must cover exactly") for error in errors)


def test_rejects_placeholder_build_identity() -> None:
    result = passing_result()
    result["silicon_revision"] = "unknown"
    result["firmware_commit"] = "TBD"
    errors = MODULE.validate_result(result)
    assert "silicon_revision must not be placeholder provenance" in errors
    assert "firmware_commit must not be placeholder provenance" in errors
