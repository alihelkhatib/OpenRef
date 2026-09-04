#!/usr/bin/env python3
"""Compile and execute vendor-independent firmware C unit tests."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
TESTS = {
    "watchdog_fg23": [
        "firmware/system/common/openref_watchdog_gate.c",
        "firmware/prototype0/fg23/src/openref_watchdog_fg23.c",
        "firmware/prototype0/fg23/src/openref_watchdog_fg23_test.c",
    ],
    "audio_link_fg23": [
        "firmware/common/openref_audio_link.c",
        "firmware/common/openref_audio_transport.c",
        "firmware/prototype0/fg23/src/openref_audio_link_fg23.c",
        "firmware/prototype0/fg23/src/openref_audio_link_fg23_test.c",
    ],
    "safety_output_gate": [
        "firmware/system/common/openref_safety_output_gate.c",
        "firmware/system/common/openref_safety_output_gate_test.c",
    ],
    "safety_arbiter": [
        "firmware/system/common/openref_safety_arbiter.c",
        "firmware/system/common/openref_safety_arbiter_test.c",
    ],
    "system_safety_integration": [
        "firmware/system/common/openref_power_supervisor.c",
        "firmware/system/common/openref_startup_supervisor.c",
        "firmware/system/common/openref_accessory_monitor.c",
        "firmware/system/common/openref_safety_arbiter.c",
        "firmware/system/common/openref_system_safety_integration_test.c",
    ],
    "service_session": [
        "firmware/system/common/openref_service_session.c",
        "firmware/system/common/openref_service_session_test.c",
    ],
    "update_verifier": [
        "firmware/system/common/openref_update_verifier.c",
        "firmware/system/common/openref_update_verifier_test.c",
    ],
    "device_lifecycle": [
        "firmware/system/common/openref_device_lifecycle.c",
        "firmware/system/common/openref_device_lifecycle_test.c",
    ],
    "charge_supervisor": [
        "firmware/system/common/openref_charge_supervisor.c",
        "firmware/system/common/openref_charge_supervisor_test.c",
    ],
    "accessory_monitor": [
        "firmware/system/common/openref_accessory_monitor.c",
        "firmware/system/common/openref_accessory_monitor_test.c",
    ],
    "button_filter": [
        "firmware/system/common/openref_button_filter.c",
        "firmware/system/common/openref_button_filter_test.c",
    ],
    "status_policy": [
        "firmware/system/common/openref_status_policy.c",
        "firmware/system/common/openref_status_policy_test.c",
    ],
    "startup_supervisor": [
        "firmware/system/common/openref_startup_supervisor.c",
        "firmware/system/common/openref_startup_supervisor_test.c",
    ],
    "watchdog_gate": [
        "firmware/system/common/openref_watchdog_gate.c",
        "firmware/system/common/openref_watchdog_gate_test.c",
    ],
    "config_store": [
        "firmware/system/common/openref_config_store.c",
        "firmware/system/common/openref_config_store_test.c",
    ],
    "rt595_config_backend": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend_test.c",
    ],
    "boot_policy": [
        "firmware/system/common/openref_boot_policy.c",
        "firmware/system/common/openref_boot_policy_test.c",
    ],
    "rt595_boot_state": [
        "firmware/system/common/openref_config_store.c",
        "firmware/system/common/openref_boot_policy.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state_test.c",
    ],
    "rt595_factory_provisioning": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_factory_provisioning.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_factory_provisioning_test.c",
    ],
    "rt595_app_confirmation": [
        "firmware/system/common/openref_config_store.c",
        "firmware/system/common/openref_boot_policy.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_app_confirmation.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_app_confirmation_test.c",
    ],
    "volume_manager": [
        "firmware/system/common/openref_volume_manager.c",
        "firmware/system/common/openref_volume_manager_test.c",
    ],
    "diagnostics": [
        "firmware/system/common/openref_diagnostics.c",
        "firmware/system/common/openref_diagnostics_test.c",
    ],
    "power_supervisor": [
        "firmware/system/common/openref_power_supervisor.c",
        "firmware/system/common/openref_power_supervisor_test.c",
    ],
    "peer_supervisor": [
        "firmware/system/common/openref_peer_supervisor.c",
        "firmware/system/common/openref_peer_supervisor_test.c",
    ],
    "boot_counter": [
        "firmware/common/openref_boot_counter.c",
        "firmware/common/openref_boot_counter_test.c",
    ],
    "crew_session": [
        "firmware/common/openref_crew_session.c",
        "firmware/common/openref_crew_session_test.c",
    ],
    "crew_admission": [
        "firmware/common/openref_crew_session.c",
        "firmware/common/openref_crew_admission.c",
        "firmware/common/openref_crew_admission_test.c",
    ],
    "security": [
        "firmware/common/openref_security.c",
        "firmware/common/openref_security_test.c",
    ],
    "secure_network_packet": [
        "firmware/common/openref_proto0_packet.c",
        "firmware/common/openref_network_packet.c",
        "firmware/common/openref_security.c",
        "firmware/common/openref_secure_network_packet.c",
        "firmware/common/openref_secure_network_packet_test.c",
    ],
    "security_fg23_disabled": [
        "firmware/prototype0/fg23/src/openref_security_fg23.c",
        "firmware/prototype0/fg23/src/openref_security_fg23_test.c",
    ],
    "boot_counter_fg23_disabled": [
        "firmware/common/openref_boot_counter.c",
        "firmware/prototype0/fg23/src/openref_boot_counter_fg23.c",
        "firmware/prototype0/fg23/src/openref_boot_counter_fg23_test.c",
    ],
    "network": [
        "firmware/common/openref_proto0_packet.c",
        "firmware/common/openref_network.c",
        "firmware/common/openref_network_packet.c",
        "firmware/common/openref_network_test.c",
    ],
    "audio_link": [
        "firmware/common/openref_audio_link.c",
        "firmware/common/openref_audio_link_test.c",
    ],
    "audio_transport": [
        "firmware/common/openref_audio_link.c",
        "firmware/common/openref_audio_transport.c",
        "firmware/common/openref_audio_transport_test.c",
    ],
    "audio_capture": [
        "firmware/common/openref_audio_link.c",
        "firmware/audio_processor/common/openref_audio_capture.c",
        "firmware/audio_processor/common/openref_audio_capture_test.c",
    ],
    "audio_playout": [
        "firmware/common/openref_audio_link.c",
        "firmware/audio_processor/common/openref_audio_playout.c",
        "firmware/audio_processor/common/openref_audio_playout_test.c",
    ],
    "audio_mixer": [
        "firmware/audio_processor/common/openref_audio_mixer.c",
        "firmware/audio_processor/common/openref_audio_mixer_test.c",
    ],
    "audio_pipeline": [
        "firmware/common/openref_audio_link.c",
        "firmware/audio_processor/common/openref_audio_capture.c",
        "firmware/audio_processor/common/openref_audio_playout.c",
        "firmware/audio_processor/common/openref_audio_mixer.c",
        "firmware/audio_processor/common/openref_audio_pipeline.c",
        "firmware/audio_processor/common/openref_audio_pipeline_test.c",
    ],
    "audio_runtime": [
        "firmware/common/openref_audio_link.c",
        "firmware/audio_processor/common/openref_audio_capture.c",
        "firmware/audio_processor/common/openref_audio_playout.c",
        "firmware/audio_processor/common/openref_audio_mixer.c",
        "firmware/audio_processor/common/openref_audio_pipeline.c",
        "firmware/audio_processor/common/openref_audio_runtime.c",
        "firmware/audio_processor/common/openref_audio_runtime_test.c",
    ],
    "audio_benchmark": [
        "firmware/common/openref_audio_link.c",
        "firmware/audio_processor/common/openref_audio_capture.c",
        "firmware/audio_processor/common/openref_audio_playout.c",
        "firmware/audio_processor/common/openref_audio_mixer.c",
        "firmware/audio_processor/common/openref_audio_pipeline.c",
        "firmware/audio_processor/common/openref_audio_runtime.c",
        "firmware/audio_processor/benchmark/openref_audio_benchmark.c",
        "firmware/audio_processor/benchmark/openref_audio_benchmark_test.c",
    ],
    "rt595_lc3_adapter": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_lc3.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_lc3_test.c",
    ],
    "rt595_audio_spi": [
        "firmware/common/openref_audio_link.c",
        "firmware/common/openref_audio_transport.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_spi.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_spi_test.c",
    ],
    "rt595_update_staging": [
        "firmware/system/common/openref_update_verifier.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging_test.c",
    ],
    "rt595_update_delivery": [
        "firmware/system/common/openref_update_verifier.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_delivery.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_delivery_test.c",
    ],
    "rt595_audio_io": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_io.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_io_test.c",
    ],
    "rt595_board_resources": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_board_resources_test.c",
    ],
    "rt595_output_guard": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_output_guard.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_output_guard_test.c",
    ],
    "rt595_update_crypto": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_crypto.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_crypto_test.c",
    ],
    "rt595_slot_authenticator": [
        "firmware/system/common/openref_update_verifier.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator_test.c",
    ],
    "rt595_boot_coordinator": [
        "firmware/system/common/openref_config_store.c",
        "firmware/system/common/openref_boot_policy.c",
        "firmware/system/common/openref_update_verifier.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_coordinator.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_coordinator_test.c",
    ],
    "rt595_boot_handoff": [
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_handoff.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_handoff_test.c",
    ],
    "rt595_bootstrap": [
        "firmware/system/common/openref_config_store.c",
        "firmware/system/common/openref_boot_policy.c",
        "firmware/system/common/openref_update_verifier.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_coordinator.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_bootstrap.c",
        "firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_bootstrap_test.c",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run portable firmware C tests")
    parser.add_argument("--zig", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["ZIG_GLOBAL_CACHE_DIR"] = str(args.output_dir / "global-cache")
    environment["ZIG_LOCAL_CACHE_DIR"] = str(args.output_dir / "local-cache")
    common = [
        str(args.zig), "cc", "-std=c17", "-Wall", "-Wextra", "-Werror",
        "-Ifirmware/common", "-Ifirmware/audio_processor/common",
        "-Ifirmware/audio_processor/benchmark",
        "-Ifirmware/prototype0/fg23/src",
        "-Ifirmware/audio_processor/targets/mimxrt595_evk/test_support",
        "-Ifirmware/audio_processor/targets/mimxrt595_evk",
        "-Ifirmware/system/common",
    ]
    for name, sources in TESTS.items():
        executable = args.output_dir / f"{name}.exe"
        subprocess.run(
            [*common, *sources, "-o", str(executable)],
            cwd=ROOT,
            env=environment,
            check=True,
        )
        subprocess.run([str(executable)], cwd=ROOT, check=True)
        print(f"PASS {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
