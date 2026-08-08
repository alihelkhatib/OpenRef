from __future__ import annotations

from itertools import count

from .capacity import estimate_capacity
from .engine import Simulation
from .medium import SharedMedium
from .metrics import summarize
from .node import NodeConfig, VoiceConfig, VoiceNode
from .protocol import CoordinatorConfig, CoordinatorProtocol
from .scenario import FaultSpec, Scenario


def _voice_config(scenario: Scenario) -> VoiceConfig:
    return VoiceConfig(
        frame_interval_us=scenario.frame_interval_us,
        payload_bytes=scenario.payload_bytes,
        bitrate_bps=scenario.radio_bitrate_bps,
        overhead_bytes=scenario.overhead_bytes,
        preamble_us=scenario.preamble_us,
        stop_generation_at_us=scenario.duration_us,
        max_queue_frames=scenario.max_queue_frames,
        deadline_us=scenario.audio_deadline_us,
    )


def _coordinator_config(scenario: Scenario) -> CoordinatorConfig:
    return CoordinatorConfig(
        initial_coordinator_id=scenario.initial_coordinator_id,
        heartbeat_interval_us=scenario.heartbeat_interval_us,
        heartbeat_timeout_us=scenario.heartbeat_timeout_us,
        election_delay_us=scenario.election_delay_us,
        bitrate_bps=scenario.radio_bitrate_bps,
        overhead_bytes=scenario.overhead_bytes,
        preamble_us=scenario.preamble_us,
    )


def _require_fault_node(nodes: dict[int, VoiceNode], fault: FaultSpec) -> VoiceNode:
    if fault.node_id not in nodes:
        raise ValueError(f"Fault references unknown node_id: {fault.node_id}")
    return nodes[fault.node_id]


def _schedule_faults(
    simulation: Simulation,
    medium: SharedMedium,
    nodes: dict[int, VoiceNode],
    faults: tuple[FaultSpec, ...],
) -> None:
    for fault in faults:
        if fault.action == "disable_node":
            node = _require_fault_node(nodes, fault)
            simulation.schedule_at(
                fault.time_us,
                lambda n=node: n.set_enabled(False),
                "disable node",
            )
        elif fault.action == "enable_node":
            node = _require_fault_node(nodes, fault)
            simulation.schedule_at(
                fault.time_us,
                lambda n=node: n.set_enabled(True),
                "enable node",
            )
        elif fault.action == "packet_loss":
            if fault.probability is None:
                raise ValueError("packet_loss faults require probability")
            medium.add_loss_window(fault.time_us, fault.duration_us, fault.probability)
        else:
            raise ValueError(f"Unknown fault action: {fault.action}")


def run_scenario(scenario: Scenario) -> tuple[Simulation, dict[str, object]]:
    simulation = Simulation()
    medium = SharedMedium(
        simulation,
        scenario.propagation_delay_us,
        random_seed=scenario.random_seed,
        base_loss=scenario.packet_loss_probability,
    )
    packet_ids = count(1)
    nodes: dict[int, VoiceNode] = {}
    voice = _voice_config(scenario)

    for index, spec in enumerate(scenario.nodes):
        node = VoiceNode(
            simulation,
            medium,
            NodeConfig(spec.node_id, index * scenario.slot_spacing_us, spec.drift_ppm),
            voice,
            packet_ids=packet_ids,
        )
        nodes[spec.node_id] = node
        node.start()

    protocol = CoordinatorProtocol(
        simulation,
        medium,
        nodes,
        _coordinator_config(scenario),
        packet_ids=packet_ids,
    )
    protocol.start()

    _schedule_faults(simulation, medium, nodes, scenario.faults)

    capacity = estimate_capacity(scenario)
    simulation.run(scenario.duration_us + capacity.voice_airtime_us)
    summary = summarize(simulation.trace)
    summary.update(
        {
            "voice_airtime_us": capacity.voice_airtime_us,
            "heartbeat_airtime_us": capacity.heartbeat_airtime_us,
            "scheduled_channel_utilization": (
                capacity.scheduled_channel_utilization
            ),
            "slot_guard_us": capacity.slot_guard_us,
            "schedule_span_us": capacity.schedule_span_us,
        }
    )
    return simulation, summary
