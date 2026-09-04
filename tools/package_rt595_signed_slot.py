#!/usr/bin/env python3
"""Create and independently verify OpenRef RT595 signed slot packages.

The production signing key is an input only.  It is never generated, copied, or
written by this tool.  ECDSA uses RFC 6979 deterministic nonces and a canonical
low-S, fixed-width, big-endian r||s signature.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import re
import struct
import sys
import uuid
from pathlib import Path

from provision_rt595_trust_anchor import parse_pem

MANIFEST_BYTES = 144
SIGNED_BYTES = 80
SECTOR_BYTES = 4096
TARGET_AUDIO = 2
MAGIC = b"ORUP"
FORMAT_VERSION = 1
P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
G = (0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
     0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5)
OID_EC = bytes.fromhex("06072a8648ce3d0201")
OID_P256 = bytes.fromhex("06082a8648ce3d030107")


def _tlv(data: bytes, offset: int, tag: int) -> tuple[bytes, int]:
    if offset >= len(data) or data[offset] != tag:
        raise ValueError(f"expected DER tag 0x{tag:02x}")
    offset += 1
    if offset >= len(data):
        raise ValueError("truncated DER length")
    length = data[offset]
    offset += 1
    if length & 0x80:
        count = length & 0x7F
        if count == 0 or count > 2 or offset + count > len(data):
            raise ValueError("invalid DER length")
        length = int.from_bytes(data[offset:offset + count], "big")
        offset += count
        if length < 128:
            raise ValueError("non-canonical DER length")
    end = offset + length
    if end > len(data):
        raise ValueError("truncated DER value")
    return data[offset:end], end


def _point_add(p1: tuple[int, int] | None, p2: tuple[int, int] | None):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if p1 == p2:
        slope = (3 * x1 * x1 + A) * pow(2 * y1, -1, P) % P
    else:
        slope = (y2 - y1) * pow((x2 - x1) % P, -1, P) % P
    x3 = (slope * slope - x1 - x2) % P
    return x3, (slope * (x1 - x3) - y1) % P


def _point_mul(k: int, point=G):
    result = None
    while k:
        if k & 1:
            result = _point_add(result, point)
        point = _point_add(point, point)
        k >>= 1
    return result


def _parse_private_pem(text: str) -> tuple[int, bytes]:
    """Strictly parse unencrypted PKCS#8 EC P-256 PRIVATE KEY."""
    match = re.fullmatch(
        r"\s*-----BEGIN PRIVATE KEY-----\s*([A-Za-z0-9+/=\s]+)"
        r"-----END PRIVATE KEY-----\s*", text)
    if not match:
        raise ValueError("expected one unencrypted PKCS#8 PRIVATE KEY")
    try:
        der = base64.b64decode("".join(match.group(1).split()), validate=True)
    except Exception as exc:
        raise ValueError("invalid PEM base64") from exc
    outer, end = _tlv(der, 0, 0x30)
    if end != len(der):
        raise ValueError("trailing PKCS#8 data")
    version, pos = _tlv(outer, 0, 0x02)
    alg, pos = _tlv(outer, pos, 0x30)
    private, pos = _tlv(outer, pos, 0x04)
    if pos != len(outer) or version != b"\x00":
        raise ValueError("unsupported PKCS#8 structure")
    oid1, q = _tlv(alg, 0, 0x06)
    oid2, q = _tlv(alg, q, 0x06)
    if q != len(alg) or bytes((0x06, len(oid1))) + oid1 != OID_EC or \
            bytes((0x06, len(oid2))) + oid2 != OID_P256:
        raise ValueError("private key must be EC prime256v1/P-256")
    ec, end = _tlv(private, 0, 0x30)
    if end != len(private):
        raise ValueError("trailing EC private-key data")
    ec_version, q = _tlv(ec, 0, 0x02)
    scalar, q = _tlv(ec, q, 0x04)
    if ec_version != b"\x01" or len(scalar) != 32 or not (1 <= int.from_bytes(scalar, "big") < N):
        raise ValueError("invalid P-256 private scalar")
    d = int.from_bytes(scalar, "big")
    x, y = _point_mul(d)
    public = x.to_bytes(32, "big") + y.to_bytes(32, "big")
    # OpenSSL normally includes the optional RFC 5915 publicKey [1]. Accept it
    # only in its canonical uncompressed form and prove it matches the scalar.
    if q != len(ec):
        tagged, q = _tlv(ec, q, 0xA1)
        bits, end = _tlv(tagged, 0, 0x03)
        if q != len(ec) or end != len(tagged) or bits != b"\x00\x04" + public:
            raise ValueError("EC public key does not match private scalar")
    return d, public


def _rfc6979(d: int, digest: bytes) -> int:
    x = d.to_bytes(32, "big")
    h1 = (int.from_bytes(digest, "big") % N).to_bytes(32, "big")
    v, k = b"\x01" * 32, b"\x00" * 32
    k = hmac.new(k, v + b"\x00" + x + h1, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    k = hmac.new(k, v + b"\x01" + x + h1, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    while True:
        v = hmac.new(k, v, hashlib.sha256).digest()
        candidate = int.from_bytes(v, "big")
        if 1 <= candidate < N:
            return candidate
        k = hmac.new(k, v + b"\x00", hashlib.sha256).digest()
        v = hmac.new(k, v, hashlib.sha256).digest()


def _sign(d: int, data: bytes) -> bytes:
    digest = hashlib.sha256(data).digest()
    z = int.from_bytes(digest, "big")
    nonce = _rfc6979(d, digest)
    r = _point_mul(nonce)[0] % N
    s = pow(nonce, -1, N) * (z + r * d) % N
    if not r or not s:
        raise ValueError("invalid ECDSA result")
    s = min(s, N - s)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def _verify(public: bytes, data: bytes, signature: bytes) -> bool:
    if len(public) != 64 or len(signature) != 64:
        return False
    q = (int.from_bytes(public[:32], "big"), int.from_bytes(public[32:], "big"))
    if q[0] >= P or q[1] >= P or (q[1] ** 2 - q[0] ** 3 - A * q[0] - B) % P:
        return False
    r, s = int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")
    if not (1 <= r < N and 1 <= s <= N // 2):
        return False
    z = int.from_bytes(hashlib.sha256(data).digest(), "big")
    w = pow(s, -1, N)
    point = _point_add(_point_mul(z * w % N), _point_mul(r * w % N, q))
    return point is not None and point[0] % N == r


def _u32(value: str | int, name: str, *, nonzero=True) -> int:
    try:
        number = int(value, 0) if isinstance(value, str) else value
    except ValueError as exc:
        raise ValueError(f"{name} is not an integer") from exc
    if number < (1 if nonzero else 0) or number > 0xFFFFFFFF:
        raise ValueError(f"{name} is outside uint32 bounds")
    return number


def _layout(path: Path, slot: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    erase = data.get("erase_bytes", "0")
    if (int(erase, 0) if isinstance(erase, str) else int(erase)) != SECTOR_BYTES:
        raise ValueError("layout erase size must be 4096 bytes")
    parts = {p["name"]: p for p in data.get("partitions", [])}
    prefix = f"slot_{slot.lower()}_"
    try:
        manifest, image = parts[prefix + "manifest"], parts[prefix + "image"]
    except KeyError as exc:
        raise ValueError(f"layout has no complete slot {slot}") from exc
    mb, ms = int(manifest["base"], 0), int(manifest["size"], 0)
    ib, capacity = int(image["base"], 0), int(image["size"], 0)
    if ms != SECTOR_BYTES or ib != mb + SECTOR_BYTES or \
            manifest.get("role") != "signed_manifest_commit" or \
            image.get("role") != "candidate_image":
        raise ValueError("layout violates manifest-sector/image adjacency contract")
    return {"manifest_base": mb, "image_base": ib, "capacity": capacity}


def _release_id(text: str) -> bytes:
    try:
        raw = uuid.UUID(text).bytes
    except ValueError:
        try:
            raw = bytes.fromhex(text)
        except ValueError as exc:
            raise ValueError("release ID must be a UUID or 32 hex digits") from exc
    if len(raw) != 16 or not any(raw):
        raise ValueError("release ID must be a nonzero 16-byte value")
    return raw


def create_package(args) -> dict:
    slot = args.slot.upper()
    region = _layout(args.layout, slot)
    image = args.image.read_bytes()
    if not image or len(image) > region["capacity"]:
        raise ValueError(f"image size must be 1..{region['capacity']} bytes")
    hardware = _u32(args.hardware_id, "hardware ID")
    version = _u32(args.image_version, "image version")
    minimum = _u32(args.minimum_bootloader_version, "minimum bootloader version")
    floor = _u32(args.antirollback_floor, "antirollback floor", nonzero=False)
    confirmed = _u32(args.confirmed_image_version, "confirmed image version", nonzero=False)
    if version < floor or version <= confirmed:
        raise ValueError("image version violates rollback/confirmed-version policy")
    if args.maximum_bootloader_version is not None and minimum > _u32(
            args.maximum_bootloader_version, "maximum bootloader version"):
        raise ValueError("minimum bootloader version exceeds declared maximum")
    d, public = _parse_private_pem(args.private_key.read_text(encoding="ascii"))
    key_id = hashlib.sha256(public).digest()[:8]
    digest = hashlib.sha256(image).digest()
    if not any(key_id) or not any(digest):
        raise ValueError("derived key ID or image digest is forbidden all-zero value")
    signed = (MAGIC + bytes((FORMAT_VERSION, TARGET_AUDIO, 0, 0)) +
              struct.pack("<IIII", hardware, version, minimum, len(image)) +
              digest + _release_id(args.release_id) + key_id)
    if len(signed) != SIGNED_BYTES:
        raise AssertionError("manifest contract drift")
    manifest = signed + _sign(d, signed)
    sector = manifest + b"\xff" * (SECTOR_BYTES - len(manifest))
    package = sector + image
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(package)
    metadata = {
        "schema": "openref-rt595-signed-slot-v1", "slot": slot,
        "manifest_base": f"0x{region['manifest_base']:08x}",
        "image_base": f"0x{region['image_base']:08x}",
        "image_capacity": region["capacity"], "image_size": len(image),
        "hardware_id": f"0x{hardware:08x}", "image_version": version,
        "minimum_bootloader_version": minimum, "target": TARGET_AUDIO,
        "signing_antirollback_floor": floor,
        "signing_confirmed_image_version": confirmed,
        "release_id": signed[56:72].hex(), "key_id": key_id.hex(),
        "image_sha256": digest.hex(), "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "package_sha256": hashlib.sha256(package).hexdigest(), "package_bytes": len(package),
        "signature_format": "ECDSA-P256-SHA256 raw-r||s big-endian canonical-low-S",
    }
    metadata_path = args.metadata or args.output.with_suffix(args.output.suffix + ".json")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="ascii", newline="\n")
    return metadata


def verify_package(args) -> dict:
    slot = args.slot.upper()
    region = _layout(args.layout, slot)
    package = args.package.read_bytes()
    if len(package) <= SECTOR_BYTES or len(package) > SECTOR_BYTES + region["capacity"]:
        raise ValueError("package length is outside the selected slot")
    manifest, padding, image = package[:MANIFEST_BYTES], package[MANIFEST_BYTES:SECTOR_BYTES], package[SECTOR_BYTES:]
    if any(byte != 0xFF for byte in padding):
        raise ValueError("manifest-sector padding is not erased 0xff")
    if manifest[:4] != MAGIC or manifest[4] != FORMAT_VERSION or manifest[5] != TARGET_AUDIO or manifest[6:8] != b"\0\0":
        raise ValueError("invalid manifest header")
    hardware, version, minimum, image_size = struct.unpack_from("<IIII", manifest, 8)
    if image_size != len(image):
        raise ValueError("manifest image size does not equal package image size")
    expected_hardware = _u32(args.hardware_id, "hardware ID")
    bootloader = _u32(args.bootloader_version, "bootloader version")
    floor = _u32(args.antirollback_floor, "antirollback floor", nonzero=False)
    confirmed = _u32(args.confirmed_image_version, "confirmed image version", nonzero=False)
    if hardware != expected_hardware:
        raise ValueError("hardware ID mismatch")
    if minimum > bootloader:
        raise ValueError("bootloader version is below manifest minimum")
    if version < floor or version <= confirmed:
        raise ValueError("image version violates rollback/confirmed-version policy")
    _, public = parse_pem(args.public_key.read_text(encoding="ascii"))
    if manifest[72:80] != hashlib.sha256(public).digest()[:8]:
        raise ValueError("manifest key ID does not match public key")
    if not any(manifest[24:56]) or not any(manifest[72:80]):
        raise ValueError("manifest digest or key ID is zero")
    if not any(manifest[56:72]):
        raise ValueError("release ID is zero")
    if hashlib.sha256(image).digest() != manifest[24:56]:
        raise ValueError("image digest mismatch")
    if not _verify(public, manifest[:SIGNED_BYTES], manifest[SIGNED_BYTES:]):
        raise ValueError("signature verification failed")
    return {"valid": True, "slot": slot, "hardware_id": f"0x{hardware:08x}",
            "image_version": version, "image_size": image_size,
            "image_sha256": manifest[24:56].hex(), "key_id": manifest[72:80].hex(),
            "package_sha256": hashlib.sha256(package).hexdigest()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pack = sub.add_parser("pack")
    pack.add_argument("--layout", type=Path, required=True); pack.add_argument("--slot", choices=("A", "B", "a", "b"), required=True)
    pack.add_argument("--image", type=Path, required=True); pack.add_argument("--private-key", type=Path, required=True)
    pack.add_argument("--hardware-id", default="0x59500001"); pack.add_argument("--image-version", required=True)
    pack.add_argument("--minimum-bootloader-version", default="1"); pack.add_argument("--maximum-bootloader-version")
    pack.add_argument("--antirollback-floor", required=True); pack.add_argument("--confirmed-image-version", required=True)
    pack.add_argument("--release-id", required=True); pack.add_argument("--output", type=Path, required=True); pack.add_argument("--metadata", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("--layout", type=Path, required=True); verify.add_argument("--slot", choices=("A", "B", "a", "b"), required=True)
    verify.add_argument("--package", type=Path, required=True); verify.add_argument("--public-key", type=Path, required=True)
    verify.add_argument("--hardware-id", default="0x59500001"); verify.add_argument("--bootloader-version", default="1")
    verify.add_argument("--antirollback-floor", default="0"); verify.add_argument("--confirmed-image-version", default="0")
    args = parser.parse_args(argv)
    try:
        result = create_package(args) if args.command == "pack" else verify_package(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
