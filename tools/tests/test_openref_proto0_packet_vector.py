import struct


def test_proto0_header_reference_vector() -> None:
    encoded = struct.pack(
        "<HBBBBHQH",
        0x4F52,
        1,
        1,
        2,
        0,
        0x1234,
        0x0102030405060708,
        60,
    )

    assert len(encoded) == 18
    assert encoded.hex() == "524f01010200341208070605040302013c00"
