from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import queue
import threading
import time

from capture_serial import _load_serial
from railtest_packet_run import parse_last_event_fields, run_packet_check
from railtest_pair_smoke import drain_text, reader, write_command
from railtest_smoke import discover_segger_serial_ports


def _status_int(status: dict[str, str], key: str) -> int:
    try:
        return int(status.get(key, "0"), 0)
    except ValueError:
        return 0


def run_rx_overflow_recovery_probe(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    rf_path: int | None,
    overflow_delay_us: int,
    stress_packets: int,
    stress_tx_delay_ms: int,
    recovery_packets: int,
    payload_bytes: int,
    reset_after_overflow: bool,
    summary_json: Path | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    rx_log = output_dir / f"{run_id}-railtest-rx-overflow-{rx_port.lower()}-rx.log"
    tx_log = output_dir / f"{run_id}-railtest-rx-overflow-{tx_port.lower()}-tx.log"
    recovery_summary = output_dir / f"{run_id}-railtest-rx-overflow-recovery-summary.json"

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()

    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        with serial.Serial(tx_port, baudrate=baud, timeout=0.1) as tx_handle:
            rx_thread = threading.Thread(target=reader, args=(rx_handle, rx_log, stop, rx_sink), daemon=True)
            tx_thread = threading.Thread(target=reader, args=(tx_handle, tx_log, stop, tx_sink), daemon=True)
            rx_thread.start()
            tx_thread.start()
            time.sleep(0.5)

            for handle in (rx_handle, tx_handle):
                write_command(handle, "rx 0")
                write_command(handle, "setNotifications 1")
            time.sleep(0.3)
            if rf_path is not None:
                write_command(rx_handle, f"setRfPath {rf_path}")
                write_command(tx_handle, f"setRfPath {rf_path}")
                time.sleep(0.3)

            for command in ("resetCounters", f"setRxOverflow 1 {overflow_delay_us}", "rx 1"):
                write_command(rx_handle, command)
                time.sleep(0.25)
            for command in (
                "resetCounters",
                f"setTxLength {payload_bytes}",
                f"setTxDelay {stress_tx_delay_ms}",
                f"tx {stress_packets}",
            ):
                write_command(tx_handle, command)
                time.sleep(0.25)

            time.sleep(3.0)
            write_command(rx_handle, "status")
            time.sleep(0.4)
            for command in ("setRxOverflow 0", "rx 0", "fifoReset 1 1", "status"):
                write_command(rx_handle, command)
                time.sleep(0.4)
            tx_recovery_commands = ["tx 0", "tx 0", "rx 0", "setTxDelay 100", "status"]
            if reset_after_overflow:
                tx_recovery_commands.append("reset")
            for command in tx_recovery_commands:
                write_command(tx_handle, command)
                time.sleep(0.3)
            if reset_after_overflow:
                write_command(rx_handle, "reset")
                time.sleep(3.0)

            stop.set()
            rx_thread.join(timeout=2)
            tx_thread.join(timeout=2)

    rx_text = drain_text(rx_sink)
    induced_status = parse_last_event_fields(rx_text, "status")
    # The final status after disabling RX is useful for state recovery; scan all
    # captured status objects to preserve the highest induced overflow counter.
    rx_overflow = 0
    no_rx_buffer = 0
    frame_errors = 0
    for chunk in rx_text.split("{{(status)}"):
        fields = parse_last_event_fields("{{(status)}" + chunk, "status")
        rx_overflow = max(rx_overflow, _status_int(fields, "RxOverflow"))
        no_rx_buffer = max(no_rx_buffer, _status_int(fields, "NoRxBuffer"))
        frame_errors = max(frame_errors, _status_int(fields, "FrameErrors"))

    induced_fault_observed = any(value > 0 for value in (rx_overflow, no_rx_buffer, frame_errors))
    recovery_result = run_packet_check(
        rx_port=rx_port,
        tx_port=tx_port,
        output_dir=output_dir,
        baud=baud,
        packets=recovery_packets,
        payload_bytes=payload_bytes,
        tx_delay_ms=20,
        settle_seconds=8,
        rf_path=rf_path,
        summary_json=recovery_summary,
    )
    recovery = json.loads(recovery_summary.read_text(encoding="utf-8"))
    passed = bool(induced_fault_observed and recovery_result == 0)

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rx_port": rx_port,
        "tx_port": tx_port,
        "rf_path": rf_path,
        "overflow_delay_us": overflow_delay_us,
        "stress_packets": stress_packets,
        "stress_tx_delay_ms": stress_tx_delay_ms,
        "recovery_packets": recovery_packets,
        "payload_bytes": payload_bytes,
        "reset_after_overflow": reset_after_overflow,
        "induced_fault_observed": induced_fault_observed,
        "max_rx_overflow": rx_overflow,
        "max_no_rx_buffer": no_rx_buffer,
        "max_frame_errors": frame_errors,
        "final_rf_state": induced_status.get("RfState"),
        "recovery_pass": recovery_result == 0,
        "recovery_delivery_ratio": recovery.get("delivery_ratio"),
        "recovery_rx_count": recovery.get("rx_count"),
        "recovery_transmitted_packets": recovery.get("transmitted_packets"),
        "pass": passed,
        "rx_log": str(rx_log),
        "tx_log": str(tx_log),
        "recovery_summary": str(recovery_summary),
    }
    rendered = json.dumps(summary, indent=2, sort_keys=True)
    print(rendered)
    if summary_json is not None:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if passed else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Force RAILtest RX overflow and verify packet recovery."
    )
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--rf-path", type=int, choices=(0, 1), default=0)
    parser.add_argument("--overflow-delay-us", type=int, default=100000)
    parser.add_argument("--stress-packets", type=int, default=100)
    parser.add_argument("--stress-tx-delay-ms", type=int, default=1)
    parser.add_argument("--recovery-packets", type=int, default=25)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument(
        "--no-reset-after-overflow",
        action="store_true",
        help="Attempt recovery without rebooting after the induced overflow.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("firmware/prototype0/fg23/results"))
    parser.add_argument("--summary-json", type=Path)
    args = parser.parse_args()

    if args.overflow_delay_us < 1:
        parser.error("--overflow-delay-us must be at least 1")
    if args.stress_packets < 1 or args.recovery_packets < 1:
        parser.error("packet counts must be at least 1")
    if args.stress_tx_delay_ms < 1:
        parser.error("--stress-tx-delay-ms must be at least 1")
    if args.payload_bytes < 1 or args.payload_bytes > 255:
        parser.error("--payload-bytes must be between 1 and 255")

    ports = discover_segger_serial_ports()
    rx_port = args.rx_port or (ports[0] if len(ports) >= 1 else None)
    tx_port = args.tx_port or (ports[1] if len(ports) >= 2 else None)
    if rx_port is None or tx_port is None or rx_port == tx_port:
        print(
            "FAIL: provide two distinct ports with --rx-port and --tx-port, "
            f"or connect two SEGGER serial devices. Found: {', '.join(ports) or 'none'}"
        )
        raise SystemExit(1)

    raise SystemExit(
        run_rx_overflow_recovery_probe(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            rf_path=args.rf_path,
            overflow_delay_us=args.overflow_delay_us,
            stress_packets=args.stress_packets,
            stress_tx_delay_ms=args.stress_tx_delay_ms,
            recovery_packets=args.recovery_packets,
            payload_bytes=args.payload_bytes,
            reset_after_overflow=not args.no_reset_after_overflow,
            summary_json=args.summary_json,
        )
    )


if __name__ == "__main__":
    main()
