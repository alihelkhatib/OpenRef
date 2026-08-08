from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import queue
import threading
import time

from capture_serial import _load_serial
from railtest_smoke import discover_segger_serial_ports


def write_command(handle, command: str) -> None:
    handle.write(f"{command}\r\n".encode("utf-8"))
    handle.flush()


def reader(handle, log_path: Path, stop: threading.Event, sink: queue.Queue[str]) -> None:
    with log_path.open("w", encoding="utf-8", newline="") as log:
        log.write(f"# capture_start_utc={datetime.now(timezone.utc).isoformat()}\n")
        log.flush()
        while not stop.is_set():
            raw = handle.readline()
            if not raw:
                continue
            text = raw.decode("utf-8", errors="replace")
            sink.put(text)
            log.write(text)
            log.flush()
        log.write(f"# capture_end_utc={datetime.now(timezone.utc).isoformat()}\n")


def drain_text(sink: queue.Queue[str]) -> str:
    chunks = []
    while True:
        try:
            chunks.append(sink.get_nowait())
        except queue.Empty:
            break
    return "".join(chunks)


def output_has_packet_exchange(rx_text: str, tx_text: str) -> bool:
    return "rxPacket" in rx_text and ("txEnd" in tx_text or "txPacket" in tx_text)


def tx_wait_seconds(
    *, packets: int, tx_delay_ms: int | None, settle_seconds: float
) -> float:
    if tx_delay_ms is None or packets <= 0:
        return settle_seconds
    expected_tx_seconds = packets * tx_delay_ms / 1000
    return max(settle_seconds, expected_tx_seconds + 5.0)


def run_pair_smoke(
    *,
    rx_port: str,
    tx_port: str,
    output_dir: Path,
    baud: int,
    packets: int,
    payload_bytes: int,
    tx_delay_ms: int | None,
    settle_seconds: float,
    rf_path: int | None,
) -> int:
    serial, _ = _load_serial()
    output_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y%m%d")
    rx_log = output_dir / f"{date}-railtest-pair-rx.log"
    tx_log = output_dir / f"{date}-railtest-pair-tx.log"

    rx_sink: queue.Queue[str] = queue.Queue()
    tx_sink: queue.Queue[str] = queue.Queue()
    stop = threading.Event()

    with serial.Serial(rx_port, baudrate=baud, timeout=0.1) as rx_handle:
        with serial.Serial(tx_port, baudrate=baud, timeout=0.1) as tx_handle:
            rx_thread = threading.Thread(
                target=reader,
                args=(rx_handle, rx_log, stop, rx_sink),
                daemon=True,
            )
            tx_thread = threading.Thread(
                target=reader,
                args=(tx_handle, tx_log, stop, tx_sink),
                daemon=True,
            )
            rx_thread.start()
            tx_thread.start()

            write_command(rx_handle, "rx 0")
            write_command(tx_handle, "rx 0")
            time.sleep(0.3)

            if rf_path is not None:
                write_command(rx_handle, f"setRfPath {rf_path}")
                write_command(tx_handle, f"setRfPath {rf_path}")
                time.sleep(0.3)

            for command in ("resetCounters", "setNotifications 1", "rx 1"):
                write_command(rx_handle, command)
                time.sleep(0.2)

            for command in (
                "resetCounters",
                "setNotifications 1",
                *( [f"setTxDelay {tx_delay_ms}"] if tx_delay_ms is not None else [] ),
                f"setTxLength {payload_bytes}",
                f"tx {packets}",
            ):
                write_command(tx_handle, command)
                time.sleep(0.2)

            time.sleep(
                tx_wait_seconds(
                    packets=packets,
                    tx_delay_ms=tx_delay_ms,
                    settle_seconds=settle_seconds,
                )
            )
            write_command(rx_handle, "status")
            write_command(tx_handle, "status")
            time.sleep(0.5)
            write_command(rx_handle, "rx 0")
            time.sleep(0.2)

            stop.set()
            rx_thread.join(timeout=2)
            tx_thread.join(timeout=2)

    rx_text = drain_text(rx_sink)
    tx_text = drain_text(tx_sink)
    if output_has_packet_exchange(rx_text, tx_text):
        print(f"PASS: packet exchange observed ({packets} TX request)")
        print(f"RX log: {rx_log}")
        print(f"TX log: {tx_log}")
        return 0

    print("FAIL: packet exchange markers missing")
    print(f"RX log: {rx_log}")
    print(f"TX log: {tx_log}")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a two-board FG23 RAILtest TX/RX smoke test."
    )
    parser.add_argument("--rx-port")
    parser.add_argument("--tx-port")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--packets", type=int, default=20)
    parser.add_argument("--payload-bytes", type=int, default=60)
    parser.add_argument("--tx-delay-ms", type=int)
    parser.add_argument("--settle-seconds", type=float, default=5)
    parser.add_argument("--rf-path", type=int, choices=(0, 1))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("firmware/prototype0/fg23/results"),
    )
    args = parser.parse_args()

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
        run_pair_smoke(
            rx_port=rx_port,
            tx_port=tx_port,
            output_dir=args.output_dir,
            baud=args.baud,
            packets=args.packets,
            payload_bytes=args.payload_bytes,
            tx_delay_ms=args.tx_delay_ms,
            settle_seconds=args.settle_seconds,
            rf_path=args.rf_path,
        )
    )


if __name__ == "__main__":
    main()
