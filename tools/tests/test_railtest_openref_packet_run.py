from __future__ import annotations

from railtest_openref_packet_run import (
    build_openref_packet,
    extract_rx_payloads,
    parse_openref_packet,
    payload_commands,
)


def test_build_and_parse_openref_packet() -> None:
    packet = build_openref_packet(
        source_id=1,
        destination_id=2,
        sequence=0x1234,
        timestamp_us=0x0102030405060708,
        payload_bytes=4,
    )

    assert packet.hex() == "524f0101010234120807060504030201040034353637"
    header = parse_openref_packet(packet)
    assert header is not None
    assert header.sequence == 0x1234
    assert header.payload_length == 4


def test_payload_commands_chunk_bytes_for_railtest() -> None:
    commands = payload_commands(bytes(range(20)), chunk_size=8)

    assert commands == [
        "setTxLength 20",
        "setTxPayloadQuiet 0 0 1 2 3 4 5 6 7",
        "setTxPayloadQuiet 8 8 9 10 11 12 13 14 15",
        "setTxPayloadQuiet 16 16 17 18 19",
    ]


def test_extract_rx_payloads() -> None:
    text = """
    {{(rxPacket)}{len:3}{crc:Pass}{payload: 0x52 0x4f 0x01}}
    {{(rxPacket)}{len:2}{crc:Pass}{payload: 0xaa 0xbb}}
    """

    assert extract_rx_payloads(text) == [b"RO\x01", b"\xaa\xbb"]
