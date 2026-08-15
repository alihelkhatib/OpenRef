import hashlib
import json
import sys
from pathlib import Path

import pytest

from package_audio_benchmark_evidence import main, package_evidence


def test_packager_records_relative_files_and_real_hashes(tmp_path: Path) -> None:
    artifacts = {}
    for key, name in (("serial_log", "run.log"), ("elf", "app.elf"), ("map", "app.map")):
        path = tmp_path / name
        path.write_bytes(key.encode())
        artifacts[key] = path
    result = package_evidence({"schema": "openref-audio-benchmark-v2"}, artifacts, tmp_path)
    assert result["artifact_files"]["elf"] == "app.elf"
    assert result["artifact_sha256"]["map"] == hashlib.sha256(b"map").hexdigest()


def test_packager_rejects_empty_and_outside_artifacts(tmp_path: Path) -> None:
    inside = tmp_path / "inside"
    inside.mkdir()
    files = {}
    for key in ("serial_log", "elf", "map"):
        path = inside / key
        path.write_bytes(key.encode())
        files[key] = path
    files["elf"] = tmp_path / "outside.elf"
    files["elf"].write_bytes(b"elf")
    with pytest.raises(ValueError, match="outside"):
        package_evidence({}, files, inside)
    files["elf"] = inside / "elf"
    files["map"].write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        package_evidence({}, files, inside)


def test_cli_refuses_to_replace_existing_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "raw.json"
    source.write_text(json.dumps({"schema": "openref-audio-benchmark-v2"}), encoding="utf-8")
    artifacts = []
    for name in ("serial.log", "app.elf", "app.map"):
        path = tmp_path / name
        path.write_bytes(name.encode())
        artifacts.append(path)
    output = tmp_path / "result.json"
    output.write_text("preserve", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "package_audio_benchmark_evidence.py", str(source),
        "--serial-log", str(artifacts[0]), "--elf", str(artifacts[1]),
        "--map", str(artifacts[2]), "--output", str(output),
    ])
    assert main() == 1
    assert output.read_text(encoding="utf-8") == "preserve"
