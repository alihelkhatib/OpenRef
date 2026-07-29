from __future__ import annotations

from itertools import count

from .engine import Simulation
from .medium import SharedMedium
from .metrics import summarize
from .node import NodeConfig, VoiceNode
from .packet import packet_airtime_us
from .protocol import CoordinatorProtocol
from .scenario import Scenario


def run_scenario(scenario: Scenario):
    simulation = Simulation()
    medium = SharedMedium(simulation, scenario.propagation_delay_us, random_seed=scenario.random_seed, base_loss=scenario.packet_loss_probability)
    packet_ids = count(1)
    nodes: dict[int, VoiceNode] = {}
    for index, spec in enumerate(scenario.nodes):
        node = VoiceNode(
            simulation, medium,
            NodeConfig(spec.node_id, index * scenario.slot_spacing_us, spec.drift_ppm),
            frame_interval_us=scenario.frame_interval_us,
            payload_bytes=scenario.payload_bytes,
            bitrate_bps=scenario.radio_bitrate_bps,
            overhead_bytes=scenario.overhead_bytes,
            preamble_us=scenario.preamble_us,
            packet_ids=packet_ids,
            stop_generation_at_us=scenario.duration_us,
            max_queue_frames=scenario.max_queue_frames,
            deadline_us=scenario.audio_deadline_us,
        )
        nodes[spec.node_id] = node
        node.start()

    protocol = CoordinatorProtocol(
        simulation, medium, nodes,
        initial_coordinator_id=scenario.initial_coordinator_id,
        heartbeat_interval_us=scenario.heartbeat_interval_us,
        heartbeat_timeout_us=scenario.heartbeat_timeout_us,
        election_delay_us=scenario.election_delay_us,
        packet_ids=packet_ids,
        bitrate_bps=scenario.radio_bitrate_bps,
        overhead_bytes=scenario.overhead_bytes,
        preamble_us=scenario.preamble_us,
    )
    protocol.start()

    for fault in scenario.faults:
        if fault.action == "disable_node" and fault.node_id is not None:
            simulation.schedule_at(fault.time_us, lambda n=nodes[fault.node_id]: n.set_enabled(False), "disable node")
        elif fault.action == "enable_node" and fault.node_id is not None:
            simulation.schedule_at(fault.time_us, lambda n=nodes[fault.node_id]: n.set_enabled(True), "enable node")
        elif fault.action == "packet_loss" and fault.probability is not None:
            medium.add_loss_window(fault.time_us, fault.duration_us, fault.probability)

    final_airtime = packet_airtime_us(scenario.payload_bytes, scenario.radio_bitrate_bps, scenario.overhead_bytes, scenario.preamble_us)
    simulation.run(scenario.duration_us + final_airtime)
    return simulation, summarize(simulation.trace)
