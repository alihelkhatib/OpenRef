import struct
from pathlib import Path


ROOT = Path(__file__).parents[2]


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def test_audio_link_reference_vector() -> None:
    header = struct.pack(
        "<HBBBBHIHBB",
        0x414F,
        1,
        2,
        3,
        0x03,
        0x1234,
        0x01020304,
        80,
        2,
        0,
    )
    body = header + bytes(range(80))
    encoded = body + struct.pack("<H", crc16_ccitt(body))

    assert len(header) == 16
    assert len(encoded) == 98
    assert encoded[:16].hex() == "4f410102030334120403020150000200"
    assert encoded[-2:].hex() == "aa0a"


def test_firmware_contract_matches_reference_sizes() -> None:
    header = (ROOT / "firmware/common/openref_audio_link.h").read_text()
    assert "OPENREF_AUDIO_LINK_HEADER_BYTES 16u" in header
    assert "OPENREF_AUDIO_LINK_PAYLOAD_BYTES 80u" in header
    assert "OPENREF_AUDIO_LINK_FRAME_BYTES 98u" in header
    assert "OPENREF_AUDIO_LINK_QUEUE_CAPACITY 4u" in header

