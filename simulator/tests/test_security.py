import pytest
from cryptography.exceptions import InvalidTag

from openref_sim.security import build_nonce, open_payload, protect_payload


KEY = bytes(range(16))
HEADER = bytes.fromhex("524f0102010001000000000000006000ffff")
PLAINTEXT = bytes(range(80))


def test_security_envelope_round_trip_and_vector() -> None:
    envelope = protect_payload(
        KEY, HEADER, PLAINTEXT,
        crew_session_id=0x01020304, source_id=1,
        boot_counter=0x11121314, packet_counter=0x21222324,
    )
    assert len(envelope) == 96
    assert envelope.hex() == (
        "14131211242322219467a7b7a9c4780c2ff037cef149e62f"
        "244d1073ab90fc6d45a7166b1bb1688097639913fdc6a07a3"
        "06c7b42338ddd23697672fc21874171ea6127c76706497657"
        "e20e0fc9193020acc80d708c318eb39eda6ef13ea6b2e5"
    )
    assert open_payload(
        KEY, HEADER, envelope, crew_session_id=0x01020304, source_id=1
    ) == (0x11121314, 0x21222324, PLAINTEXT)


def test_authentication_rejects_modified_header_or_tag() -> None:
    envelope = protect_payload(
        KEY, HEADER, PLAINTEXT,
        crew_session_id=7, source_id=2, boot_counter=3, packet_counter=4,
    )
    with pytest.raises(InvalidTag):
        open_payload(KEY, HEADER[:-1] + b"\x00", envelope, crew_session_id=7, source_id=2)
    with pytest.raises(InvalidTag):
        open_payload(KEY, HEADER, envelope[:-1] + bytes([envelope[-1] ^ 1]), crew_session_id=7, source_id=2)


def test_nonce_changes_for_each_uniqueness_input() -> None:
    baseline = build_nonce(1, 1, 1, 1)
    assert len(baseline) == 13
    assert len({baseline, build_nonce(2, 1, 1, 1), build_nonce(1, 2, 1, 1),
                build_nonce(1, 1, 2, 1), build_nonce(1, 1, 1, 2)}) == 5
