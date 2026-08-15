"""Reference implementation of the OpenRef Prototype 0 security envelope."""

from __future__ import annotations

import struct

from cryptography.hazmat.primitives.ciphers.aead import AESCCM


NONCE_BYTES = 13
PREFIX_BYTES = 8
TAG_BYTES = 8
_PREFIX = struct.Struct("<II")


def build_nonce(
    crew_session_id: int,
    source_id: int,
    boot_counter: int,
    packet_counter: int,
) -> bytes:
    if not 0 <= crew_session_id <= 0xFFFFFFFF:
        raise ValueError("crew_session_id must fit in 32 bits")
    if not 1 <= source_id <= 0xFE:
        raise ValueError("source_id must identify a node from 1 through 254")
    if not 0 <= boot_counter <= 0xFFFFFFFF:
        raise ValueError("boot_counter must fit in 32 bits")
    if not 0 <= packet_counter <= 0xFFFFFFFF:
        raise ValueError("packet_counter must fit in 32 bits")
    return struct.pack("<IBII", crew_session_id, source_id, boot_counter, packet_counter)


def protect_payload(
    key: bytes,
    header: bytes,
    plaintext: bytes,
    *,
    crew_session_id: int,
    source_id: int,
    boot_counter: int,
    packet_counter: int,
) -> bytes:
    """Return the clear counter prefix followed by ciphertext and an 8-byte tag."""
    nonce = build_nonce(crew_session_id, source_id, boot_counter, packet_counter)
    protected = AESCCM(key, tag_length=TAG_BYTES).encrypt(nonce, plaintext, header)
    return _PREFIX.pack(boot_counter, packet_counter) + protected


def open_payload(
    key: bytes,
    header: bytes,
    envelope: bytes,
    *,
    crew_session_id: int,
    source_id: int,
) -> tuple[int, int, bytes]:
    """Authenticate and decrypt an envelope without maintaining replay state."""
    if len(envelope) < PREFIX_BYTES + TAG_BYTES:
        raise ValueError("security envelope is truncated")
    boot_counter, packet_counter = _PREFIX.unpack_from(envelope)
    nonce = build_nonce(crew_session_id, source_id, boot_counter, packet_counter)
    plaintext = AESCCM(key, tag_length=TAG_BYTES).decrypt(
        nonce, envelope[PREFIX_BYTES:], header
    )
    return boot_counter, packet_counter, plaintext
