from __future__ import annotations

from dataclasses import dataclass

from .packet import packet_airtime_us
from .scenario import Scenario


@dataclass(frozen=True)
class CapacityEstimate:
    voice_airtime_us: int
    heartbeat_airtime_us: int
    voice_channel_utilization: float
    heartbeat_channel_utilization: float
    scheduled_channel_utilization: float
    slot_guard_us: int
    schedule_span_us: int


def estimate_capacity(scenario: Scenario) -> CapacityEstimate:
    voice_airtime_us = packet_airtime_us(
        scenario.payload_bytes,
        scenario.radio_bitrate_bps,
        scenario.overhead_bytes,
        scenario.preamble_us,
    )
    heartbeat_airtime_us = packet_airtime_us(
        8,
        scenario.radio_bitrate_bps,
        scenario.overhead_bytes,
        scenario.preamble_us,
    )
    voice_utilization = (
        scenario.node_count * voice_airtime_us / scenario.frame_interval_us
    )
    heartbeat_utilization = heartbeat_airtime_us / scenario.heartbeat_interval_us
    return CapacityEstimate(
        voice_airtime_us=voice_airtime_us,
        heartbeat_airtime_us=heartbeat_airtime_us,
        voice_channel_utilization=voice_utilization,
        heartbeat_channel_utilization=heartbeat_utilization,
        scheduled_channel_utilization=voice_utilization + heartbeat_utilization,
        slot_guard_us=scenario.slot_spacing_us - voice_airtime_us,
        schedule_span_us=(scenario.node_count - 1) * scenario.slot_spacing_us
        + voice_airtime_us,
    )
