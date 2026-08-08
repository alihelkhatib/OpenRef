from __future__ import annotations

import pytest

from openref_autorole_run import parse_nm_symbol_address


def test_parse_nm_symbol_address() -> None:
    output = "200045fc B other\n20004610 B openref_app_role\n"

    assert parse_nm_symbol_address(output) == 0x20004610


def test_parse_nm_symbol_address_rejects_missing_symbol() -> None:
    with pytest.raises(ValueError):
        parse_nm_symbol_address("200045fc B other\n")


def test_parse_nm_symbol_address_accepts_named_symbol() -> None:
    output = "20004610 B openref_app_role\n20004614 B openref_app_payload_bytes\n"

    assert parse_nm_symbol_address(output, symbol="openref_app_payload_bytes") == 0x20004614
