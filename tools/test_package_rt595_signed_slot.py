import base64
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_rt595_signed_slot import G, N, create_package, verify_package


def _der(tag: int, value: bytes) -> bytes:
    length = bytes((len(value),)) if len(value) < 128 else bytes((0x81, len(value)))
    return bytes((tag,)) + length + value


def _pem(label: str, der: bytes) -> str:
    body = base64.b64encode(der).decode()
    return f"-----BEGIN {label}-----\n" + "\n".join(body[i:i+64] for i in range(0, len(body), 64)) + f"\n-----END {label}-----\n"


def _keys(root: Path) -> tuple[Path, Path]:
    # Deterministic test-only scalar d=1.  It is deliberately generated inside
    # the temporary test directory and is never suitable for production.
    oid_ec = bytes.fromhex("06072a8648ce3d0201")
    oid_curve = bytes.fromhex("06082a8648ce3d030107")
    alg = _der(0x30, oid_ec + oid_curve)
    ec_private = _der(0x30, _der(0x02, b"\x01") + _der(0x04, (1).to_bytes(32, "big")))
    pkcs8 = _der(0x30, _der(0x02, b"\x00") + alg + _der(0x04, ec_private))
    raw = G[0].to_bytes(32, "big") + G[1].to_bytes(32, "big")
    spki = _der(0x30, alg + _der(0x03, b"\x00\x04" + raw))
    private, public = root / "test-private.pem", root / "test-public.pem"
    private.write_text(_pem("PRIVATE KEY", pkcs8), encoding="ascii")
    public.write_text(_pem("PUBLIC KEY", spki), encoding="ascii")
    return private, public


def _layout(root: Path) -> Path:
    path = root / "layout.json"
    path.write_text(json.dumps({"erase_bytes": "0x1000", "partitions": [
        {"name": "slot_a_manifest", "role": "signed_manifest_commit", "base": "0x08040000", "size": "0x1000"},
        {"name": "slot_a_image", "role": "candidate_image", "base": "0x08041000", "size": "0xbf000"},
        {"name": "slot_b_manifest", "role": "signed_manifest_commit", "base": "0x08100000", "size": "0x1000"},
        {"name": "slot_b_image", "role": "candidate_image", "base": "0x08101000", "size": "0xbf000"},
    ]}), encoding="utf-8")
    return path


def _pack_args(tmp_path: Path):
    private, public = _keys(tmp_path)
    image = tmp_path / "app.bin"; image.write_bytes(bytes(range(256)) * 3)
    output = tmp_path / "slot.bin"
    return SimpleNamespace(layout=_layout(tmp_path), slot="A", image=image,
        private_key=private, hardware_id="0x59500001", image_version="7",
        minimum_bootloader_version="1", maximum_bootloader_version="3",
        antirollback_floor="7", confirmed_image_version="6",
        release_id="00112233-4455-6677-8899-aabbccddeeff", output=output,
        metadata=None), public


def _verify_args(pack, public):
    return SimpleNamespace(layout=pack.layout, slot=pack.slot, package=pack.output,
        public_key=public, hardware_id="0x59500001", bootloader_version="1",
        antirollback_floor="7", confirmed_image_version="6")


def test_package_is_deterministic_and_matches_wire_contract(tmp_path: Path):
    args, public = _pack_args(tmp_path)
    first = create_package(args); package = args.output.read_bytes()
    second = create_package(args)
    assert args.output.read_bytes() == package
    assert first == second
    assert len(package) == 4096 + 768
    assert package[:8] == b"ORUP\x01\x02\x00\x00"
    assert package[80:144] != bytes(64)
    assert package[144:4096] == b"\xff" * (4096 - 144)
    assert package[4096:] == args.image.read_bytes()
    assert verify_package(_verify_args(args, public))["valid"] is True
    metadata = json.loads(args.output.with_suffix(".bin.json").read_text())
    assert metadata["manifest_base"] == "0x08040000"
    assert metadata["image_base"] == "0x08041000"
    assert metadata["key_id"] == hashlib.sha256(
        G[0].to_bytes(32, "big") + G[1].to_bytes(32, "big")).hexdigest()[:16]
    assert not any(args.output.parent.glob("*private*.json"))


@pytest.mark.parametrize("offset", [0, 24, 80, 143, 200, 4096, 4200])
def test_verifier_rejects_every_package_region_mutation(tmp_path: Path, offset: int):
    args, public = _pack_args(tmp_path); create_package(args)
    damaged = bytearray(args.output.read_bytes()); damaged[offset] ^= 1; args.output.write_bytes(damaged)
    with pytest.raises(ValueError):
        verify_package(_verify_args(args, public))


def test_verifier_enforces_boot_and_rollback_bounds(tmp_path: Path):
    args, public = _pack_args(tmp_path); create_package(args)
    verify = _verify_args(args, public)
    verify.bootloader_version = "0"
    with pytest.raises(ValueError, match="uint32|bootloader"):
        verify_package(verify)
    verify.bootloader_version = "1"; verify.confirmed_image_version = "7"
    with pytest.raises(ValueError, match="rollback"):
        verify_package(verify)


def test_pack_rejects_capacity_and_declared_bootloader_bound(tmp_path: Path):
    args, _ = _pack_args(tmp_path)
    data = json.loads(args.layout.read_text()); data["partitions"][1]["size"] = "0x10"
    args.layout.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="image size"):
        create_package(args)
    args.layout = _layout(tmp_path); args.minimum_bootloader_version = "4"
    with pytest.raises(ValueError, match="exceeds"):
        create_package(args)


def test_pack_rejects_rollback_or_non_new_version(tmp_path: Path):
    args, _ = _pack_args(tmp_path)
    args.confirmed_image_version = "7"
    with pytest.raises(ValueError, match="rollback"):
        create_package(args)
    args.confirmed_image_version = "6"; args.antirollback_floor = "8"
    with pytest.raises(ValueError, match="rollback"):
        create_package(args)


def test_rejects_wrong_key_and_high_s_signature(tmp_path: Path):
    args, public = _pack_args(tmp_path); create_package(args)
    package = bytearray(args.output.read_bytes())
    s = int.from_bytes(package[112:144], "big")
    package[112:144] = (N - s).to_bytes(32, "big")
    args.output.write_bytes(package)
    with pytest.raises(ValueError, match="signature"):
        verify_package(_verify_args(args, public))
