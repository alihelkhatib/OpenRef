import pytest

from openref_sim.packet import (
    OPENREF_BROADCAST_ID,
    WireHeader,
    WirePacketKind,
    decode_wire_packet,
    encode_wire_packet,
    packet_airtime_us,
)


def test_airtime_rounds_up() -> None:
    assert packet_airtime_us(60, 500_000, 16, 100) == 1316


def test_wire_header_matches_firmware_reference_vector() -> None:
    header = WireHeader(WirePacketKind.PING, 2, OPENREF_BROADCAST_ID, 0x1234, 0x0102030405060708, 60)
    assert header.encode().hex() == "524f01010200341208070605040302013c00"


def test_wire_packet_round_trip() -> None:
    payload = bytes(range(48))
    expected = WireHeader(WirePacketKind.AUDIO_FRAME, 3, OPENREF_BROADCAST_ID, 65535, 20_000, len(payload))
    header, decoded_payload = decode_wire_packet(encode_wire_packet(expected, payload))
    assert header == expected
    assert decoded_payload == payload


@pytest.mark.parametrize(
    ("packet", "message"),
    [
        (b"\x00" * 17, "shorter"),
        (bytes.fromhex("000001010200000000000000000000000000"), "magic"),
        (bytes.fromhex("524f02010200000000000000000000000000"), "version"),
        (bytes.fromhex("524f01630200000000000000000000000000"), "kind"),
        (bytes.fromhex("524f01010200000000000000000000000100"), "truncated"),
    ],
)
def test_wire_packet_rejects_malformed_input(packet: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        decode_wire_packet(packet)


def test_wire_packet_rejects_spoofable_source_zero() -> None:
    header = WireHeader(WirePacketKind.CONTROL, 0, 0, 1, 0, 0)
    with pytest.raises(ValueError, match="source_id"):
        header.encode()
