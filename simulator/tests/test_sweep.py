import argparse
from pathlib import Path

import pytest

from openref_sim.scenario import load_scenario
from openref_sim.sweep import (
    format_sweep_markdown,
    parse_float_values,
    parse_int_values,
    sweep_scenario,
)


SCENARIOS = Path(__file__).parents[1] / "scenarios"


def test_parse_sweep_values() -> None:
    assert parse_float_values("10, 20") == (10.0, 20.0)
    assert parse_int_values("16000,24000") == (16_000, 24_000)

    with pytest.raises(argparse.ArgumentTypeError):
        parse_int_values("")


def test_sweep_sorts_feasible_cases_first() -> None:
    base = load_scenario(SCENARIOS / "six_nodes_nominal.yaml")
    results = sweep_scenario(
        base,
        frame_durations_ms=(20.0,),
        encoded_bitrates_bps=(24_000,),
        radio_bitrates_bps=(500_000,),
        slot_spacings_us=(500, 2_500),
    )

    by_slot = {result.slot_spacing_us: result for result in results}
    assert by_slot[500].feasible is False
    assert by_slot[2_500].feasible is True
    assert results[0].slot_spacing_us == 2_500


def test_sweep_markdown_respects_limit() -> None:
    base = load_scenario(SCENARIOS / "six_nodes_nominal.yaml")
    results = sweep_scenario(
        base,
        frame_durations_ms=(20.0,),
        encoded_bitrates_bps=(24_000,),
        radio_bitrates_bps=(500_000,),
        slot_spacings_us=(500, 2_500),
    )

    markdown = format_sweep_markdown(results, limit=1)
    assert "frame_ms" in markdown
    assert markdown.count("| yes |") == 1
    assert "| no |" not in markdown
