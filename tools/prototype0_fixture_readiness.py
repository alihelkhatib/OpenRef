from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_AUDIO_EVENTS = {
    "impulse",
    "capture_frame",
    "packet_queue",
    "tx_start",
    "rx_done",
    "playback_output",
}

READINESS_SCHEMA = "prototype0-fixture-readiness-v1"

DEFAULT_AUDIO_EVENT_ALIASES = {
    "impulse": "impulse",
    "capture": "capture_frame",
    "queue": "packet_queue",
    "tx_start": "tx_start",
    "rx": "rx_done",
    "playback": "playback_output",
}


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


PLACEHOLDER_FRAGMENTS = (
    "yyyy",
    "describe",
    "model",
    "attenuator db",
    "shielding method",
    "electrical or acoustic",
)


def _is_filled_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    lowered = text.lower()
    return not any(fragment in lowered for fragment in PLACEHOLDER_FRAGMENTS)


def _has_suffix(value: Any, suffix: str) -> bool:
    return _is_filled_text(value) and Path(value).suffix.lower() == suffix


def _as_posix_path(value: Any) -> str:
    return str(value).replace("\\", "/")


def _summary_json_for_csv(value: str) -> str:
    return _as_posix_path(Path(value).with_suffix(".summary.json"))


def _attenuation_summary_json(value: str) -> str:
    path = Path(value)
    name = path.name
    for suffix in (
        "-step-00-baseline.json",
        "-baseline.json",
    ):
        if name.endswith(suffix):
            return _as_posix_path(path.with_name(name[: -len(suffix)] + "-attenuation-summary.json"))
    return _as_posix_path(path.with_name(path.stem + "-attenuation-summary.json"))


def command_text(command: list[str]) -> str:
    rendered: list[str] = []
    for item in command:
        if not item or any(char.isspace() for char in item) or "'" in item:
            rendered.append("'" + item.replace("'", "''") + "'")
        else:
            rendered.append(item)
    return " ".join(rendered)


def _coerce_set_value(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if value.startswith(("{", "[")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def apply_set(data: dict[str, Any], assignment: str) -> None:
    if "=" not in assignment:
        raise ValueError(f"assignment must be path=value: {assignment}")
    path, raw_value = assignment.split("=", 1)
    parts = [part for part in path.split(".") if part]
    if not parts:
        raise ValueError(f"assignment path is empty: {assignment}")

    target: Any = data
    for part in parts[:-1]:
        if isinstance(target, list):
            if not part.isdigit():
                raise ValueError(f"list path segment must be numeric: {assignment}")
            target = target[int(part)]
        elif isinstance(target, dict):
            if part not in target:
                raise ValueError(f"unknown assignment path: {assignment}")
            target = target[part]
        else:
            raise ValueError(f"assignment path cannot descend through scalar: {assignment}")

    leaf = parts[-1]
    value = _coerce_set_value(raw_value)
    if isinstance(target, list):
        if not leaf.isdigit():
            raise ValueError(f"list path segment must be numeric: {assignment}")
        target[int(leaf)] = value
    elif isinstance(target, dict):
        if leaf not in target:
            raise ValueError(f"unknown assignment path: {assignment}")
        target[leaf] = value
    else:
        raise ValueError(f"assignment path cannot set scalar: {assignment}")


def _parse_step_assignment(assignment: str) -> dict[str, str]:
    parts = [part.strip() for part in assignment.split(",") if part.strip()]
    step: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            raise ValueError(f"attenuated step item must be key=value: {assignment}")
        key, value = part.split("=", 1)
        key = key.strip()
        if key not in {"label", "physical_setting", "summary_json"}:
            raise ValueError(f"unsupported attenuated step key: {key}")
        step[key] = value.strip()
    missing = {"label", "physical_setting", "summary_json"} - set(step)
    if missing:
        raise ValueError("attenuated step missing: " + ", ".join(sorted(missing)))
    return step


def apply_attenuated_steps(data: dict[str, Any], assignments: list[str]) -> None:
    if not assignments:
        return
    data["attenuated_steps"] = [_parse_step_assignment(item) for item in assignments]


def _parse_audio_event_assignment(assignment: str) -> tuple[str, str]:
    if "=" not in assignment:
        raise ValueError(f"audio event assignment must be key=value: {assignment}")
    key, value = assignment.split("=", 1)
    key = key.strip()
    value = value.strip()
    if key not in DEFAULT_AUDIO_EVENT_ALIASES:
        allowed = ", ".join(sorted(DEFAULT_AUDIO_EVENT_ALIASES))
        raise ValueError(f"unsupported audio event key {key}; expected one of {allowed}")
    if not _is_filled_text(value):
        raise ValueError(f"audio event {key} must have a filled label")
    return key, value


def apply_audio_events(data: dict[str, Any], assignments: list[str]) -> None:
    if not assignments:
        return
    aliases = dict(data.get("event_aliases", DEFAULT_AUDIO_EVENT_ALIASES))
    for assignment in assignments:
        key, value = _parse_audio_event_assignment(assignment)
        aliases[key] = value
    data["event_aliases"] = aliases
    data["events"] = [aliases[key] for key in sorted(aliases)]


def template(gate: str) -> dict[str, Any]:
    if gate == "E0-03":
        return {
            "schema": READINESS_SCHEMA,
            "gate": "E0-03",
            "instrument": "logic analyzer or oscilloscope model",
            "ground_connected": False,
            "sample_rate_hz": 5_000_000,
            "channels": {"queue": "PB3", "start": "PB2"},
            "expected_samples": 100,
            "output_csv": "firmware/prototype0/fg23/results/YYYYMMDD-e0-03-scheduled-tx-gpio.csv",
            "analyzer_flags": ["--fail-on-unpaired-edges"],
        }
    if gate == "E0-05":
        return {
            "schema": READINESS_SCHEMA,
            "gate": "E0-05",
            "method": "calibrated attenuator, shield box, or repeatable shielding",
            "rf_path": 0,
            "same_direction_all_steps": True,
            "packet_count_per_step": 200,
            "baseline_summary_json": "firmware/prototype0/fg23/results/YYYYMMDD-e0-05-step-00-baseline.json",
            "attenuated_steps": [
                {
                    "label": "step-01",
                    "physical_setting": "attenuator dB or shielding method",
                    "summary_json": "firmware/prototype0/fg23/results/YYYYMMDD-e0-05-step-01.json",
                }
            ],
            "physical_setup_note": "describe fixture, cable path, spacing, enclosure, or body/shielding method",
        }
    if gate == "E0-07":
        return {
            "schema": READINESS_SCHEMA,
            "gate": "E0-07",
            "fixture_method": "electrical or acoustic loopback method",
            "firmware_timing_markers": False,
            "expected_samples": 10,
            "target_latency_ms": 120,
            "max_latency_ms": 180,
            "events": sorted(REQUIRED_AUDIO_EVENTS),
            "event_aliases": dict(DEFAULT_AUDIO_EVENT_ALIASES),
            "output_csv": "firmware/prototype0/fg23/results/YYYYMMDD-e0-07-audio-loopback.csv",
        }
    raise ValueError(f"unsupported gate {gate}")


def validate(gate: str, data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if data.get("schema") != READINESS_SCHEMA:
        failures.append(f"schema must be {READINESS_SCHEMA}")
    if data.get("gate") != gate:
        failures.append(f"gate must be {gate}")

    if gate == "E0-03":
        if not _is_filled_text(data.get("instrument")):
            failures.append("instrument is required")
        if data.get("ground_connected") is not True:
            failures.append("ground_connected must be true")
        if (_number(data.get("sample_rate_hz")) or 0) < 5_000_000:
            failures.append("sample_rate_hz must be at least 5000000")
        channels = data.get("channels") if isinstance(data.get("channels"), dict) else {}
        if channels.get("queue") != "PB3":
            failures.append("channels.queue must be PB3")
        if channels.get("start") != "PB2":
            failures.append("channels.start must be PB2")
        if (_number(data.get("expected_samples")) or 0) < 100:
            failures.append("expected_samples must be at least 100")
        if not _has_suffix(data.get("output_csv"), ".csv"):
            failures.append("output_csv must be a filled .csv path")
        analyzer_flags = data.get("analyzer_flags", [])
        if not isinstance(analyzer_flags, list) or not all(
            isinstance(item, str) for item in analyzer_flags
        ):
            failures.append("analyzer_flags must be a list of strings")
            analyzer_flags = []
        if "--fail-on-unpaired-edges" not in analyzer_flags:
            failures.append("analyzer_flags must include --fail-on-unpaired-edges")

    elif gate == "E0-05":
        if not _is_filled_text(data.get("method")):
            failures.append("method is required")
        if data.get("rf_path") != 0:
            failures.append("rf_path must be 0 for the qualified bench path")
        if data.get("same_direction_all_steps") is not True:
            failures.append("same_direction_all_steps must be true")
        if (_number(data.get("packet_count_per_step")) or 0) < 200:
            failures.append("packet_count_per_step must be at least 200")
        if not _has_suffix(data.get("baseline_summary_json"), ".json"):
            failures.append("baseline_summary_json must be a filled .json path")
        steps = data.get("attenuated_steps")
        if not isinstance(steps, list) or not steps:
            failures.append("attenuated_steps must contain at least one step")
        else:
            labels: list[str] = []
            for index, step in enumerate(steps):
                if not isinstance(step, dict):
                    failures.append(f"attenuated_steps[{index}] must be an object")
                    continue
                label = step.get("label")
                if not _is_filled_text(label):
                    failures.append(f"attenuated_steps[{index}].label is required")
                else:
                    labels.append(label.strip())
                if not _is_filled_text(step.get("physical_setting")):
                    failures.append(f"attenuated_steps[{index}].physical_setting is required")
                if not _has_suffix(step.get("summary_json"), ".json"):
                    failures.append(
                        f"attenuated_steps[{index}].summary_json must be a filled .json path"
                    )
            duplicate_labels = sorted({label for label in labels if labels.count(label) > 1})
            if duplicate_labels:
                failures.append("attenuated_steps labels must be unique")
        if not _is_filled_text(data.get("physical_setup_note")):
            failures.append("physical_setup_note is required")

    elif gate == "E0-07":
        if not _is_filled_text(data.get("fixture_method")):
            failures.append("fixture_method is required")
        if data.get("firmware_timing_markers") is not True:
            failures.append("firmware_timing_markers must be true")
        if (_number(data.get("expected_samples")) or 0) < 10:
            failures.append("expected_samples must be at least 10")
        target = _number(data.get("target_latency_ms"))
        maximum = _number(data.get("max_latency_ms"))
        if target is None or target <= 0:
            failures.append("target_latency_ms must be positive")
        if maximum is None or maximum <= 0:
            failures.append("max_latency_ms must be positive")
        if target is not None and maximum is not None and maximum < target:
            failures.append("max_latency_ms must be greater than or equal to target_latency_ms")
        aliases = data.get("event_aliases", DEFAULT_AUDIO_EVENT_ALIASES)
        if not isinstance(aliases, dict) or set(aliases) != set(DEFAULT_AUDIO_EVENT_ALIASES):
            failures.append(
                "event_aliases must contain: " + ", ".join(sorted(DEFAULT_AUDIO_EVENT_ALIASES))
            )
            aliases = {}
        elif not all(isinstance(value, str) and _is_filled_text(value) for value in aliases.values()):
            failures.append("event_aliases values must be filled strings")
            aliases = {}
        elif len(set(aliases.values())) != len(aliases):
            failures.append("event_aliases values must be unique")
        expected_events = set(aliases.values()) if aliases else REQUIRED_AUDIO_EVENTS
        raw_events = data.get("events", [])
        if not isinstance(raw_events, list) or not all(isinstance(item, str) for item in raw_events):
            failures.append("events must be a list of strings")
            raw_events = []
        if len(raw_events) != len(set(raw_events)):
            failures.append("events must not contain duplicates")
        events = set(raw_events)
        missing_events = sorted(expected_events - events)
        if missing_events:
            failures.append("events missing: " + ", ".join(missing_events))
        unexpected_events = sorted(events - expected_events)
        if unexpected_events:
            failures.append("events unexpected: " + ", ".join(unexpected_events))
        if not _has_suffix(data.get("output_csv"), ".csv"):
            failures.append("output_csv must be a filled .csv path")

    else:
        failures.append(f"unsupported gate {gate}")

    return failures


def analysis_command(gate: str, data: dict[str, Any]) -> list[str] | None:
    if gate == "E0-03":
        flags = list(data.get("analyzer_flags", []))
        return [
            "python",
            "tools/analyze_scheduled_tx_gpio.py",
            _as_posix_path(data["output_csv"]),
            "--queue-channel",
            data["channels"]["queue"],
            "--start-channel",
            data["channels"]["start"],
            "--expected-samples",
            str(data["expected_samples"]),
            *flags,
            "--json",
            _summary_json_for_csv(data["output_csv"]),
        ]
    if gate == "E0-05":
        steps = data["attenuated_steps"]
        inputs = [_as_posix_path(data["baseline_summary_json"])] + [
            _as_posix_path(step["summary_json"]) for step in steps
        ]
        labels = ["baseline"] + [step["label"] for step in steps]
        return [
            "python",
            "tools/analyze_attenuation_sweep.py",
            *inputs,
            "--labels",
            *labels,
            "--min-steps",
            str(len(inputs)),
            "--json",
            _attenuation_summary_json(data["baseline_summary_json"]),
        ]
    if gate == "E0-07":
        aliases = data.get("event_aliases", DEFAULT_AUDIO_EVENT_ALIASES)
        alias_args: list[str] = []
        for key in sorted(DEFAULT_AUDIO_EVENT_ALIASES):
            if aliases.get(key) != DEFAULT_AUDIO_EVENT_ALIASES[key]:
                alias_args.extend(["--event", f"{key}={aliases[key]}"])
        return [
            "python",
            "tools/analyze_audio_loopback.py",
            _as_posix_path(data["output_csv"]),
            "--expected-samples",
            str(data["expected_samples"]),
            "--target-latency-ms",
            str(data["target_latency_ms"]),
            "--max-latency-ms",
            str(data["max_latency_ms"]),
            *alias_args,
            "--json",
            _summary_json_for_csv(data["output_csv"]),
        ]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Prototype 0 external-fixture readiness metadata."
    )
    parser.add_argument("--gate", choices=("E0-03", "E0-05", "E0-07"), required=True)
    parser.add_argument("--template", action="store_true")
    parser.add_argument("--fill", action="store_true")
    parser.add_argument("--check", type=Path)
    parser.add_argument(
        "--set",
        dest="assignments",
        action="append",
        default=[],
        metavar="PATH=VALUE",
        help="Override template fields for --fill, e.g. channels.queue=PB3",
    )
    parser.add_argument(
        "--attenuated-step",
        action="append",
        default=[],
        metavar="label=LABEL,physical_setting=TEXT,summary_json=PATH",
        help="Replace E0-05 attenuated steps for --fill; repeat for multiple steps.",
    )
    parser.add_argument(
        "--audio-event",
        action="append",
        default=[],
        metavar="KEY=LABEL",
        help="Override E0-07 event labels for --fill, e.g. playback=audio_out.",
    )
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    if sum(1 for enabled in (args.template, args.fill, bool(args.check)) if enabled) != 1:
        parser.error("use exactly one of --template, --fill, or --check")
    if args.assignments and not args.fill:
        parser.error("--set can only be used with --fill")
    if args.attenuated_step and not args.fill:
        parser.error("--attenuated-step can only be used with --fill")
    if args.attenuated_step and args.gate != "E0-05":
        parser.error("--attenuated-step can only be used with --gate E0-05")
    if args.audio_event and not args.fill:
        parser.error("--audio-event can only be used with --fill")
    if args.audio_event and args.gate != "E0-07":
        parser.error("--audio-event can only be used with --gate E0-07")

    if args.template:
        result = template(args.gate)
        exit_code = 0
    elif args.fill:
        result = template(args.gate)
        try:
            for assignment in args.assignments:
                apply_set(result, assignment)
            apply_attenuated_steps(result, args.attenuated_step)
            apply_audio_events(result, args.audio_event)
        except ValueError as exc:
            parser.error(str(exc))
        failures = validate(args.gate, result)
        exit_code = 0 if not failures else 1
        if failures:
            result = {
                "gate": args.gate,
                "pass": False,
                "failures": failures,
                "metadata": result,
            }
    else:
        data = json.loads(args.check.read_text(encoding="utf-8"))
        failures = validate(args.gate, data)
        result = {
            "gate": args.gate,
            "input": str(args.check),
            "pass": not failures,
            "failures": failures,
        }
        if not failures:
            command = analysis_command(args.gate, data)
            result["analysis_command"] = command
            result["analysis_command_text"] = command_text(command or [])
        exit_code = 0 if not failures else 1

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
