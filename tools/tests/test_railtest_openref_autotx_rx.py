from __future__ import annotations

from railtest_openref_autotx_rx import HEADER_BYTES


def test_autotx_tool_uses_openref_header_size() -> None:
    assert HEADER_BYTES == 18
