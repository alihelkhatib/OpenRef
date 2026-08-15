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
        80,
    )

    assert len(encoded) == 18
    assert encoded.hex() == "524f01010200341208070605040302015000"


def test_network_heartbeat_reference_vector() -> None:
    header = struct.pack(
        "<HBBBBHQH",
        0x4F52,
        1,
        3,
        2,
        0,
        0x1234,
        0x0102030405060708,
        80,
    )
    heartbeat = struct.pack("<IQ", 0x01020304, 0x1112131415161718)
    encoded = header + heartbeat + bytes(68)

    assert len(encoded) == 98
    assert encoded[:30].hex() == (
        "524f01030200341208070605040302015000"
        "040302011817161514131211"
    )
