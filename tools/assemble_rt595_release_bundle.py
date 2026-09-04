#!/usr/bin/env python3
"""Assemble and independently verify a self-contained RT595 release bundle.

The bundle contains public/releasable material only.  In particular this tool
has no private-key option and rejects files which look like private keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import package_rt595_signed_slot as slot_package
from provision_rt595_trust_anchor import parse_pem
from validate_rt595_flash_layout import validate_layout

SCHEMA = "openref.rt595.release-bundle.v1"
REVIEW_SCHEMA = "openref.rt595.release-review.v1"
REQUIRED = {
    "bootstrap_binary": "bootstrap.bin",
    "application_binary": "application.bin",
    "signed_slot_package": "signed-slot.bin",
    "signed_slot_metadata": "signed-slot.json",
    "flash_layout": "flash-layout.json",
    "bootstrap_layout_report": "bootstrap-layout-report.json",
    "application_layout_report": "application-layout-report.json",
    "trust_anchor_manifest": "trust-anchor.json",
    "trust_anchor_public_key": "trust-anchor-public.pem",
    "release_provenance": "provenance.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _integer(value, name: str) -> int:
    try:
        return int(value, 0) if isinstance(value, str) else int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {name}") from exc


def _partitions(layout: dict) -> dict[str, tuple[int, int]]:
    result = {}
    for item in layout.get("partitions", []):
        result[item["name"]] = (_integer(item["base"], "partition base"),
                                _integer(item["size"], "partition size"))
    return result


def _vector_check(image: bytes, base: int, capacity: int, label: str) -> None:
    if len(image) < 8 or len(image) > capacity:
        raise ValueError(f"{label} size is outside its flash partition")
    msp, reset = struct.unpack_from("<II", image)
    if msp & 7 or not (0x20000000 <= msp < 0x40000000):
        raise ValueError(f"{label} initial MSP is invalid")
    if not reset & 1 or not (base <= (reset & ~1) < base + len(image)):
        raise ValueError(f"{label} reset vector is outside the linked image")


def _provenance_hashes(doc: dict) -> set[str]:
    if doc.get("schema") != "openref.release-provenance.v1":
        raise ValueError("unsupported release provenance schema")
    if doc.get("claims", {}).get("release_ready") is not False:
        raise ValueError("input provenance must remain non-authoritative")
    hashes = set()
    for record in doc.get("artifacts", []):
        digest = record.get("sha256")
        if isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest):
            hashes.add(digest)
    return hashes


def _layout_report(path: Path, layout_hash: str, label: str) -> None:
    report = _json(path)
    if report.get("schema") != "openref.rt595-flash-layout-validation.v1" or report.get("status") != "passed":
        raise ValueError(f"{label} layout report is not a passed canonical validation")
    if report.get("errors") != [] or report.get("layout", {}).get("sha256") != layout_hash:
        raise ValueError(f"{label} layout report does not bind the canonical layout")
    map_record = report.get("map")
    if not isinstance(map_record, dict) or not isinstance(map_record.get("bytes"), int) or map_record["bytes"] <= 0 or not re.fullmatch(r"[0-9a-f]{64}", str(map_record.get("sha256", ""))):
        raise ValueError(f"{label} layout report lacks a hashed nonempty link map")


def _review(review: dict | None, subject: dict) -> tuple[bool, str]:
    if review is None:
        return False, "independent reviewed evidence was not supplied"
    required = {"schema", "verdict", "reviewer", "reviewed_at", "bundle_subject"}
    if set(review) != required or review["schema"] != REVIEW_SCHEMA or review["verdict"] != "approved":
        raise ValueError("reviewed evidence is not a strict approved release review")
    reviewer = review["reviewer"]
    if not isinstance(reviewer, dict) or set(reviewer) != {"name", "organization", "independent"}:
        raise ValueError("reviewer identity is malformed")
    if not all(isinstance(reviewer[k], str) and reviewer[k].strip() for k in ("name", "organization")) or reviewer["independent"] is not True:
        raise ValueError("review must identify an independent reviewer")
    try:
        stamp = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("reviewed_at must be an ISO-8601 timestamp") from exc
    if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
        raise ValueError("review timestamp is naive or in the future")
    if review["bundle_subject"] != subject:
        raise ValueError("review does not bind the exact release subject")
    return True, "independent release review approved and hash-bound"


def validate_files(paths: dict[str, Path], review_path: Path | None = None) -> dict:
    for role, path in paths.items():
        if not path.is_file():
            raise ValueError(f"missing {role}: {path}")
    forbidden = (b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN EC PRIVATE KEY-----")
    for role, path in paths.items():
        if any(marker in path.read_bytes() for marker in forbidden):
            raise ValueError(f"private key material is forbidden from release bundles ({role})")
    public_text = paths["trust_anchor_public_key"].read_text(encoding="ascii")
    if "PRIVATE KEY" in public_text:
        raise ValueError("private key material is forbidden from release bundles")
    _, public = parse_pem(public_text)
    key_id = hashlib.sha256(public).digest()[:8].hex()
    trust = _json(paths["trust_anchor_manifest"])
    if trust.get("key_id_hex") != key_id or trust.get("public_key_sha256") != hashlib.sha256(public).hexdigest():
        raise ValueError("trust-anchor manifest does not match public key")
    layout = _json(paths["flash_layout"])
    layout_errors, _ = validate_layout(layout)
    if layout_errors:
        raise ValueError("canonical flash layout is invalid: " + "; ".join(layout_errors))
    layout_hash = sha256(paths["flash_layout"])
    _layout_report(paths["bootstrap_layout_report"], layout_hash, "bootstrap")
    _layout_report(paths["application_layout_report"], layout_hash, "application")
    metadata = _json(paths["signed_slot_metadata"])
    slot = metadata.get("slot")
    if slot not in {"A", "B"}:
        raise ValueError("signed-slot metadata has invalid slot")
    parts = _partitions(layout)
    try:
        bootstrap_base, bootstrap_capacity = parts["bootstrap_xip"]
        manifest_base, manifest_capacity = parts[f"slot_{slot.lower()}_manifest"]
        image_base, image_capacity = parts[f"slot_{slot.lower()}_image"]
    except KeyError as exc:
        raise ValueError("layout lacks required bootstrap/slot partitions") from exc
    if manifest_capacity != slot_package.SECTOR_BYTES or image_base != manifest_base + manifest_capacity:
        raise ValueError("layout violates signed-slot adjacency")
    application = paths["application_binary"].read_bytes()
    bootstrap = paths["bootstrap_binary"].read_bytes()
    package = paths["signed_slot_package"].read_bytes()
    if package[slot_package.SECTOR_BYTES:] != application:
        raise ValueError("signed package payload is not the application binary")
    if metadata.get("schema") != "openref-rt595-signed-slot-v1":
        raise ValueError("unsupported signed-slot metadata schema")
    expected = {
        "manifest_base": f"0x{manifest_base:08x}", "image_base": f"0x{image_base:08x}",
        "image_capacity": image_capacity, "image_size": len(application),
        "image_sha256": hashlib.sha256(application).hexdigest(),
        "package_sha256": hashlib.sha256(package).hexdigest(), "package_bytes": len(package),
        "key_id": key_id,
        "manifest_sha256": hashlib.sha256(package[:slot_package.MANIFEST_BYTES]).hexdigest(),
        "release_id": package[56:72].hex(), "target": slot_package.TARGET_AUDIO,
    }
    for field, value in expected.items():
        if metadata.get(field) != value:
            raise ValueError(f"signed-slot metadata {field} mismatch")
    # Cryptographically verify using the policy values recorded at signing.
    verify_args = argparse.Namespace(
        slot=slot, layout=paths["flash_layout"], package=paths["signed_slot_package"],
        public_key=paths["trust_anchor_public_key"], hardware_id=metadata.get("hardware_id"),
        bootloader_version=metadata.get("minimum_bootloader_version"),
        antirollback_floor=metadata.get("signing_antirollback_floor"),
        confirmed_image_version=metadata.get("signing_confirmed_image_version"),
    )
    verified = slot_package.verify_package(verify_args)
    for field in ("slot", "image_version", "image_size", "image_sha256", "key_id", "package_sha256"):
        if verified.get(field) != metadata.get(field):
            raise ValueError(f"verified package {field} mismatch")
    _vector_check(bootstrap, bootstrap_base, bootstrap_capacity, "bootstrap")
    _vector_check(application, image_base, image_capacity, "application")
    provenance_hashes = _provenance_hashes(_json(paths["release_provenance"]))
    critical = [role for role in REQUIRED if role != "release_provenance"]
    missing = [role for role in critical if sha256(paths[role]) not in provenance_hashes]
    if missing:
        raise ValueError("provenance does not bind critical artifacts: " + ", ".join(missing))
    subject = {
        "artifact_sha256": {role: sha256(path) for role, path in sorted(paths.items())},
        "bootstrap_sha256": sha256(paths["bootstrap_binary"]),
        "application_sha256": sha256(paths["application_binary"]),
        "package_sha256": sha256(paths["signed_slot_package"]),
        "provenance_sha256": sha256(paths["release_provenance"]),
        "slot": slot, "image_version": metadata["image_version"], "key_id": key_id,
    }
    review = _json(review_path) if review_path else None
    ready, reason = _review(review, subject)
    return {"subject": subject, "release_ready": ready, "readiness_reason": reason,
            "reviewed_evidence": review}


def assemble(args) -> dict:
    paths = {role: getattr(args, role) for role in REQUIRED}
    validation = validate_files(paths, args.reviewed_evidence)
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output bundle already exists (refusing to merge or overwrite)")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=output.name + ".tmp-", dir=output.parent))
    try:
        records = []
        for role, filename in REQUIRED.items():
            target = temp / filename
            shutil.copyfile(paths[role], target)
            records.append({"role": role, "file": filename, "bytes": target.stat().st_size,
                            "sha256": sha256(target)})
        if args.reviewed_evidence:
            shutil.copyfile(args.reviewed_evidence, temp / "reviewed-evidence.json")
            records.append({"role": "reviewed_evidence", "file": "reviewed-evidence.json",
                            "bytes": (temp / "reviewed-evidence.json").stat().st_size,
                            "sha256": sha256(temp / "reviewed-evidence.json")})
        manifest = {"schema": SCHEMA, "artifacts": sorted(records, key=lambda x: x["role"]), **validation}
        (temp / "bundle.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii", newline="\n")
        temp.rename(output)
        return manifest
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def verify(directory: Path) -> dict:
    directory = directory.resolve(strict=True)
    manifest = _json(directory / "bundle.json")
    if manifest.get("schema") != SCHEMA:
        raise ValueError("unsupported bundle schema")
    records = manifest.get("artifacts")
    if not isinstance(records, list) or len(records) != len(REQUIRED) + (1 if manifest.get("reviewed_evidence") else 0):
        raise ValueError("bundle artifact inventory is incomplete")
    seen = set()
    for record in records:
        role, filename = record.get("role"), record.get("file")
        expected = REQUIRED.get(role, "reviewed-evidence.json" if role == "reviewed_evidence" else None)
        if expected is None or filename != expected or role in seen:
            raise ValueError("bundle contains an unknown, renamed, or duplicate artifact")
        seen.add(role)
        path = directory / filename
        if not path.is_file() or path.stat().st_size != record.get("bytes") or sha256(path) != record.get("sha256"):
            raise ValueError(f"bundle artifact failed hash/size verification: {role}")
    if not set(REQUIRED).issubset(seen):
        raise ValueError("bundle lacks required artifacts")
    paths = {role: directory / filename for role, filename in REQUIRED.items()}
    review_path = directory / "reviewed-evidence.json" if "reviewed_evidence" in seen else None
    result = validate_files(paths, review_path)
    for field in ("subject", "release_ready", "readiness_reason", "reviewed_evidence"):
        if manifest.get(field) != result[field]:
            raise ValueError(f"bundle manifest {field} mismatch")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("assemble")
    for role in REQUIRED:
        create.add_argument("--" + role.replace("_", "-"), dest=role, type=Path, required=True)
    create.add_argument("--reviewed-evidence", type=Path)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify"); check.add_argument("bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        result = assemble(args) if args.command == "assemble" else verify(args.bundle)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    print(json.dumps({"valid": True, "release_ready": result["release_ready"],
                      "subject": result["subject"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
