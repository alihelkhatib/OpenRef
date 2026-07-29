from __future__ import annotations

from itertools import count

from .engine import Simulation
from .medium import SharedMedium
from .metrics import summarize
from .node import NodeConfig, VoiceNode
from .packet import packet_airtime_us
from .scenario import Scenario


def run_scenario(scenario: Scenario) -> tuple[Simulation, dict[str, float | int | None]]:
    simulation = Simulation()
    medium = SharedMedium(simulation, scenario.propagation_delay_us)
    packet_ids = count(1)
    nodes = [
        VoiceNode(
            simulation,
            medium,
            NodeConfig(node_id=i + 1, slot_offset_us=i * scenario.slot_spacing_us),
            frame_interval_us=scenario.frame_interval_us,
            payload_bytes=scenario.payload_bytes,
            bitrate_bps=scenario.radio_bitrate_bps,
            overhead_bytes=scenario.overhead_bytes,
            preamble_us=scenario.preamble_us,
            packet_ids=packet_ids,
            stop_generation_at_us=scenario.duration_us,
        )
        for i in range(scenario.node_count)
    ]
    for node in nodes:
        node.start()
    final_airtime_us = packet_airtime_us(
        scenario.payload_bytes,
        scenario.radio_bitrate_bps,
        scenario.overhead_bytes,
        scenario.preamble_us,
    )
    simulation.run(scenario.duration_us + final_airtime_us)
    return simulation, summarize(simulation.trace)
