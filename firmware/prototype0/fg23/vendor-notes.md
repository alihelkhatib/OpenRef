# FG23 Vendor Notes

Record exact vendor dependency details here during board bring-up.

## SDK Record

| Item | Value |
|---|---|
| Simplicity Studio version | 6.0.0 / Studio 289 |
| Gecko SDK version | Simplicity SDK 2026.6.1 |
| Vendor example project | RAIL - SoC RAILtest (`rail_soc_railtest`) |
| Example source path | Generated Simplicity Studio workspace project; do not commit local absolute workspace or SDK paths |
| Board/project target | `FG23-DK2600A` / `BRD2600A rev A03`, part OPN `EFR32FG23B010F512IM48` |
| Radio configurator profile | `PHY_Studio_868M_GMSK_500Kbps`, channels 0-20, max power `RAIL_TX_POWER_MAX`; current generated protocol config also enables Z-Wave support by default |
| Compiler/toolchain | GCC `14.2.rel1`; CMake `3.30.2`; SEGGER tooling `6.0.32`; Commander `1.24.3` |

## Prototype 0 Bring-Up Record

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Boards flashed | 2x `FG23-DK2600A` |
| Flashed image | Built `rail_soc_railtest` vendor example (`.hex`/`.s37` preferred over raw `.bin`) |
| Serial ports observed | `COM8`, `COM10` as SEGGER USB serial devices |
| Serial capture paths | `firmware/prototype0/fg23/results/20260807-node-1-e0-01.log`; `firmware/prototype0/fg23/results/20260807-node-2-e0-01.log` |
| Serial capture result | Both boards responded to `help` with RAILtest CLI output and prompt |
| Current E0-01 status | Build, flashing, and serial-output verification are complete |

## RAILtest Link Smoke Record

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| TX/RX packet smoke | Passed after antennas were attached; packet exchange observed in both directions |
| Packet smoke command | `python tools/railtest_pair_smoke.py` |
| RSSI probe command | `python tools/railtest_rssi_probe.py --rf-path 0` |
| RF path 0 observation | With antennas attached, RSSI rose strongly in both directions, about `-91/-90.5` dBm baseline to `-26.75` dBm during TX tone |
| RF path 1 observation | With antennas attached, RSSI stayed near noise floor; no useful tone-energy rise |
| Current interpretation | Serial CLI, TX scheduling, RF path 0 tone energy, and short RAILtest packet exchange work; proceed to OpenRef-owned packet-pair firmware for E0-02 |
| Durable summary | `firmware/prototype0/fg23/20260807-e0-01-link-smoke-result.md` |

## RAILtest Packet Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Command, COM8 RX | `python tools\railtest_packet_run.py --packets 100 --payload-bytes 60 --settle-seconds 30 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-packet-run-com8-rx.json` |
| Result, COM8 RX | Pass: 100 transmitted, 100 received, 100 sync detects, 0 CRC drops |
| Command, COM10 RX | `python tools\railtest_packet_run.py --rx-port COM10 --tx-port COM8 --packets 100 --payload-bytes 60 --settle-seconds 30 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-packet-run-com10-rx.json` |
| Result, COM10 RX | Pass: 100 transmitted, 100 received, 100 sync detects, 0 CRC drops |
| Durable summary | `firmware/prototype0/fg23/20260807-railtest-packet-precheck-result.md` |
| Analyzer bridge | Converted latest RAILtest RX log with `tools/railtest_to_packet_csv.py`; analyzer reported 100 received packets, 0 sequence gaps, 0 RX gap events, mean RSSI -27.92 dBm, mean LQI 255 |

## RAILtest 20 ms Packet Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Command, COM8 RX | `python tools\railtest_packet_run.py --packets 1500 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 35 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-1500pkt-20ms-com8-rx.json` |
| Result, COM8 RX | Pass: 1500 transmitted, 1500 received, 1500 sync detects, 0 CRC drops |
| Command, COM10 RX | `python tools\railtest_packet_run.py --rx-port COM10 --tx-port COM8 --packets 1500 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 35 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-1500pkt-20ms-com10-rx.json` |
| Result, COM10 RX | Pass: 1500 transmitted, 1500 received, 1500 sync detects, 0 CRC drops |
| Logging note | RAILtest counters are complete; verbose serial notification capture retained 1489 of 1500 latest RX packet lines at this rate |
| Durable summary | `firmware/prototype0/fg23/20260807-railtest-1500pkt-20ms-result.md` |

## RAILtest Scheduled TX Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Command | `python tools\railtest_scheduled_tx_probe.py --port COM8 --count 10 --relative-delay-us 50000 --spacing-seconds 0.25 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-scheduled-tx-com8.json` |
| Result | Pass: 10 requested, 10 TX end events, 0 aborts, 0 blocked, 0 underflows |
| Limitation | This is only an API-path precheck; E0-03 still requires external GPIO timing measurement |
| Durable summary | `firmware/prototype0/fg23/20260807-railtest-scheduled-tx-precheck-result.md` |

## OpenRef Scheduled TX SDK-Timestamp Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Runtime role | AutoRole role `3` / scheduled TX |
| Command | `python tools\openref_scheduled_tx_run.py --port COM8 --rf-path 0 --attempts 100 --payload-bytes 60 --timeout-seconds 20 --summary-json firmware\prototype0\fg23\results\20260807-openref-scheduled-tx-com8-summary.json` |
| Result | Pass: 100 queued, 100 TX started, 100 TX done, 0 rejected; launch error min -3 us, mean 3.93 us, p95 4 us, p99 4 us, max 4 us |
| Bench restore | Normal non-AutoTX/non-AutoRX/non-AutoRole hook image rebuilt and flashed back to COM8 after evidence capture; two-board RAILtest smoke passed |
| Limitation | SDK timestamp precheck only; final E0-03 still requires GPIO marker wiring and external timing capture |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-scheduled-tx-sdk-result.md` |

## OpenRef Scheduled TX GPIO Marker Plan

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole -BuildMarker B0 -QueueMarker B3 -StartMarker B2 -DoneMarker A5`; then `cmake --workflow --preset project` |
| Preferred minimum capture | `PB3` queue marker and `PB2` TX-start marker |
| Optional full capture | `PB0` build, `PB3` queue, `PB2` TX-start, `PA5` TX-done |
| Analyzer command | `python tools\analyze_scheduled_tx_gpio.py firmware\prototype0\fg23\results\YYYYMMDD-e0-03-scheduled-tx-gpio.csv --queue-channel PB3 --start-channel PB2 --expected-samples 100 --fail-on-unpaired-edges --json firmware\prototype0\fg23\results\YYYYMMDD-e0-03-scheduled-tx-gpio-summary.json` |
| Pin tradeoff | `PB0`/`PB3` are shared with the LC sensor path; `PB2` is LED0; `PA5` is BTN1. Avoid VCOM, debug, PTI, Si7021 I2C, and BTN0/bootloader pins. |
| External status | Capture still requires a logic analyzer or oscilloscope connected to the breakout pads |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-scheduled-tx-gpio-marker-plan.md` |

## RAILtest Capacity Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Command | `python tools\railtest_capacity_sweep.py --payloads 16 60 120 200 --packets 200 --tx-delay-ms 20 --settle-seconds 8 --rf-path 0` |
| Result | Pass: 16, 60, 120, and 200 payload bytes each delivered 200/200 packets with 0 CRC drops |
| Limitation | Vendor-firmware precheck only; E0-04 still requires OpenRef firmware, planned sweep range, and deadline/failure criteria |
| Durable summary | `firmware/prototype0/fg23/20260807-railtest-capacity-precheck-result.md` |

## OpenRef Controlled Attenuation Analysis Plan

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Analyzer command | `python tools\analyze_attenuation_sweep.py firmware\prototype0\fg23\results\YYYYMMDD-e0-05-step-00-baseline.json firmware\prototype0\fg23\results\YYYYMMDD-e0-05-step-01-shielded.json --labels baseline shielded --min-steps 2 --min-packet-error-rate 0.01 --json firmware\prototype0\fg23\results\YYYYMMDD-e0-05-attenuation-summary.json` |
| External status | Requires controlled attenuation, shield box, or repeatable shielding method before E0-05 can be completed |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-attenuation-analysis-plan.md` |

## E0-05 Controlled Attenuation Baseline Capture

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Command | `python tools\railtest_packet_run.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 200 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 12 --output-dir firmware\prototype0\fg23\results\e0-05-baseline-com10-to-com8 --summary-json firmware\prototype0\fg23\results\20260808-e0-05-step-00-baseline.json` |
| Result | Pass: same-bench RF path 0 baseline delivered 200/200 packets, delivery ratio 1.0, zero TX failed packets, and zero RX CRC drops |
| Fixture runner state | E0-05 readiness now has 1/2 analysis inputs present; the only missing E0-05 fixture input is `firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json` |
| Limitation | Baseline is not controlled attenuation evidence by itself; E0-05 still requires a measured attenuated/shielded step under the same direction and packet settings |
| Durable outputs | `firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json`; logs under `firmware/prototype0/fg23/results/e0-05-baseline-com10-to-com8` |

## RAILtest TX Power Sweep Precheck

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Commands | Forward: `python tools\railtest_tx_power_sweep.py --rx-port COM8 --tx-port COM10 --rf-path 0 --powers-dbm 14 0 -10 --restore-power-dbm 14 --packets 50 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 8 --summary-json firmware\prototype0\fg23\results\20260808-railtest-tx-power-sweep-com8-rx-summary.json`; reverse: `python tools\railtest_tx_power_sweep.py --rx-port COM10 --tx-port COM8 --rf-path 0 --powers-dbm 10 0 -10 --restore-power-dbm 10 --packets 50 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 8 --summary-json firmware\prototype0\fg23\results\20260808-railtest-tx-power-sweep-com10-rx-summary.json` |
| Result | Pass both directions: COM10 TX requested 14/0/-10 dBm, board-reported 14.0/-0.4/-11.1 dBm; COM8 TX requested 10/0/-10 dBm, board-reported 10.0/-0.4/-11.1 dBm; every step delivered 50/50 packets with delivery ratio 1.0 and 0 CRC drops |
| Limitation | TX-power reduction is only a link-margin precheck; final E0-05 still requires controlled attenuation or repeatable shielding |
| Durable summary | `firmware/prototype0/fg23/20260808-railtest-tx-power-sweep-precheck-result.md` |

## RAILtest RSSI Path 0 Precheck

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Commands | COM8 RX: `python tools\railtest_rssi_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260808-railtest-rssi-com8-rx-com10-tx-rf0-summary.json`; COM10 RX: `python tools\railtest_rssi_probe.py --rx-port COM10 --tx-port COM8 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260808-railtest-rssi-com10-rx-com8-tx-rf0-summary.json` |
| Result | Pass: COM8 saw -94.0 dBm baseline to -22.5 dBm tone (+71.5 dB); COM10 saw -91.0 dBm baseline to -26.5 dBm tone (+64.5 dB) |
| Limitation | RSSI tone delta is an RF-path health precheck only; final E0-05 still requires controlled attenuation or repeatable shielding |
| Durable summary | `firmware/prototype0/fg23/20260808-railtest-rssi-path0-precheck-result.md` |

## RAILtest RSSI Path 1 Negative Precheck

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Commands | COM8 RX: `python tools\railtest_rssi_probe.py --rx-port COM8 --tx-port COM10 --rf-path 1 --expect no-tone --summary-json firmware\prototype0\fg23\results\20260808-railtest-rssi-com8-rx-com10-tx-rf1-summary.json`; COM10 RX: `python tools\railtest_rssi_probe.py --rx-port COM10 --tx-port COM8 --rf-path 1 --expect no-tone --summary-json firmware\prototype0\fg23\results\20260808-railtest-rssi-com10-rx-com8-tx-rf1-summary.json` |
| Result | Pass as expected negative: COM8 delta -0.25 dB and COM10 delta +3.75 dB, both below the +10.0 dB tone threshold |
| Interpretation | Use RF path 0 for the current antenna-connected bench; path 1 is not a useful RF path in this setup |
| Durable summary | `firmware/prototype0/fg23/20260808-railtest-rssi-path1-negative-precheck-result.md` |

## OpenRef Wire Format over RAILtest

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Command, COM8 RX | `python tools\railtest_openref_packet_run.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 50 --payload-bytes 60 --interval-seconds 0.35 --command-delay-seconds 0.15 --settle-seconds 1.5 --summary-json firmware\prototype0\fg23\results\20260807-openref-railtest-com8-rx-50-summary.json` |
| Result, COM8 RX | Pass: 50 requested, 50 decoded OpenRef packets, 50 unique sequences, 0 missing, 0 duplicates |
| Command, COM10 RX | `python tools\railtest_openref_packet_run.py --rx-port COM10 --tx-port COM8 --rf-path 0 --packets 50 --payload-bytes 60 --interval-seconds 0.35 --command-delay-seconds 0.15 --settle-seconds 1.5 --summary-json firmware\prototype0\fg23\results\20260807-openref-railtest-com10-rx-50-summary.json` |
| Result, COM10 RX | Pass: 50 requested, 50 decoded OpenRef packets, 50 unique sequences, 0 missing, 0 duplicates |
| Required RAILtest setting | `setFixedLength 78`; without fixed length, the active PHY/RAILtest behavior truncated received OpenRef frames to 16 bytes |
| Interpretation | OpenRef packet bytes are now proven over the real FG23 RF link in both directions; later AutoRole evidence covers the standalone OpenRef runtime |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-railtest-wire-format-result.md` |

## RAILtest Fault-Recovery Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Commands | `python tools\railtest_fault_probe.py --port COM8 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-fault-probe-com8.json`; `python tools\railtest_fault_probe.py --port COM10 --rf-path 0 --summary-json firmware\prototype0\fg23\results\20260807-railtest-fault-probe-com10.json` |
| Result | Pass: both boards returned to idle after safe RX disable and TX cancellation; each recorded one user TX abort, zero blocked TX, zero underflow, zero RX overflow |
| Limitation | Vendor-firmware precheck only; E0-06 still requires OpenRef malformed packet, queue saturation, forced reset, and bounded memory checks |
| Durable summary | `firmware/prototype0/fg23/20260807-railtest-fault-precheck-result.md` |

## OpenRef Overlay Build

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1`; then `cmake --workflow --preset project` from the generated `cmake_gcc` directory |
| Result | Pass: OpenRef packet helper and packet-pair scaffold compiled and linked into `rail_soc_railtest.out` |
| Limitation | Runtime still uses vendor RAILtest behavior until OpenRef app entry point and Silicon Labs radio adapter are implemented |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-overlay-build-result.md` |

## OpenRef App Hook Build and Flash

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Install command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim` |
| Build command | `cmake --workflow --preset project` from generated `cmake_gcc` |
| Flash target serials | SEGGER adapters `440320955`, `440320878` |
| Result | Pass: rebuilt image flashed to both boards; both printed `openrefApp Status:Linked PacketBytes:78 Sequence:1` after reset |
| Post-flash sanity | RAILtest CLI smoke passed; OpenRef 10-packet RF check passed both directions |
| Limitation | The hook is active, but packet-pair runtime still uses host-driven RAILtest CLI until the Silicon Labs radio adapter is implemented |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-app-hook-result.md` |

## OpenRef AutoTX Board-Generated Packet Test

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| AutoTX build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoTx`; then `cmake --workflow --preset project` |
| TX board | COM10 / SEGGER `440320878` |
| RX board | COM8 / SEGGER `440320955` |
| Test command | `python tools\railtest_openref_autotx_rx.py --rx-port COM8 --tx-port COM10 --rf-path 0 --expected-packets 10 --duration-seconds 8 --summary-json firmware\prototype0\fg23\results\20260807-openref-autotx-com8-rx-summary.json` |
| Result | Pass: 26 decoded board-generated OpenRef packets, 26 unique contiguous sequences, 0 gaps, 0 duplicates |
| Five-minute command | `python tools\railtest_openref_autotx_rx.py --rx-port COM8 --tx-port COM10 --rf-path 0 --expected-packets 700 --duration-seconds 300 --summary-json firmware\prototype0\fg23\results\20260807-openref-autotx-5min-com8-rx-summary.json` |
| Five-minute result | Pass: 860 decoded board-generated OpenRef packets, 860 unique contiguous sequences, 0 gaps, 0 duplicates |
| Bench restore | Normal non-AutoTX hook image rebuilt and flashed back to COM10 after evidence capture |
| Limitation | RX decoding/counters are still PC-side log parsing in this step; later AutoRX/AutoRole evidence covers board-owned RX counters and role selection |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-autotx-result.md` |

## OpenRef AutoRX Board-Side Counter Test

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| RX build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRx`; then `cmake --workflow --preset project` |
| TX build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoTx`; then `cmake --workflow --preset project` |
| RX board | COM8 / SEGGER `440320955` |
| TX board | COM10 / SEGGER `440320878` |
| Short command | `python tools\openref_autorx_marker_run.py --rx-port COM8 --tx-port COM10 --duration-seconds 30 --expected-rx 50 --summary-json firmware\prototype0\fg23\results\20260807-openref-autorx-com8-summary.json` |
| Short result | Pass: board-side RX counter reached 200, sequence 200, 0 gaps, 0 faults |
| Five-minute command | `python tools\openref_autorx_marker_run.py --rx-port COM8 --tx-port COM10 --duration-seconds 300 --expected-rx 700 --summary-json firmware\prototype0\fg23\results\20260807-openref-autorx-5min-com8-summary.json` |
| Five-minute result | Pass: board-side RX counter reached 1100, sequence 1100, 0 gaps, 0 faults |
| Bench restore | Normal non-AutoTX/non-AutoRX hook image rebuilt and flashed back to both boards after evidence capture |
| Limitation | This step still required rebuilding/flashing role-specific images; later AutoRole evidence covers same-image role selection and the one-hour E0-02 run |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-autorx-result.md` |

## OpenRef AutoRole Same-Image Test

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Shared build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Runtime role selection | Host runner resolves `openref_app_role` from `rail_soc_railtest.out` and writes role values through RAILtest `setmemw`: `1` for TX, `2` for RX |
| RX board | COM8 / SEGGER `440320955` |
| TX board | COM10 / SEGGER `440320878` |
| Short command | `python tools\openref_autorole_run.py --rx-port COM8 --tx-port COM10 --rf-path 0 --duration-seconds 30 --expected-rx 50 --summary-json firmware\prototype0\fg23\results\20260807-openref-autorole-com8-rx-summary.json` |
| Short result | Pass: board-side RX counter reached 75, sequence 75, 0 gaps, 0 faults |
| Five-minute command | `python tools\openref_autorole_run.py --rx-port COM8 --tx-port COM10 --rf-path 0 --duration-seconds 300 --expected-rx 700 --summary-json firmware\prototype0\fg23\results\20260807-openref-autorole-5min-com8-rx-summary.json` |
| Five-minute result | Pass: board-side RX counter reached 850, sequence 850, 0 gaps, 0 faults |
| One-hour command | `python tools\openref_autorole_run.py --rx-port COM8 --tx-port COM10 --rf-path 0 --duration-seconds 3600 --expected-rx 9000 --summary-json firmware\prototype0\fg23\results\20260807-openref-autorole-1hour-com8-rx-summary.json` |
| One-hour result | Pass: board-side RX counter reached 10275, sequence 10275, 0 gaps, 0 faults |
| Bench restore | Normal non-AutoTX/non-AutoRX/non-AutoRole hook image rebuilt and flashed back to both boards after evidence capture; RAILtest smoke passed |
| Limitation | Role selection is currently host-assisted through `setmemw`; product firmware still needs a durable role/config surface |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-autorole-result.md` |

## OpenRef Runtime Capacity Sweep

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Runtime controls | Host runner resolves `openref_app_role` and `openref_app_payload_bytes` from `rail_soc_railtest.out`, then writes values through RAILtest `setmemw` |
| Command | `python tools\openref_autorole_capacity_sweep.py --rx-port COM8 --tx-port COM10 --rf-path 0 --payloads 16 60 120 200 --duration-seconds 60 --expected-rx 120` |
| Result | Pass: payloads 16, 60, 120, and 200 bytes each reached 150 board-side RX packets with 0 gaps and 0 faults |
| Aggregate summary | `firmware/prototype0/fg23/results/20260807-openref-autorole-capacity-sweep-summary.json` |
| Bench restore | Normal non-AutoTX/non-AutoRX/non-AutoRole hook image rebuilt and flashed back to both boards after evidence capture; RAILtest smoke passed |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-runtime-capacity-result.md` |

## OpenRef Role-Cycle Recovery Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Command | `python tools\openref_autorole_recovery_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --cycles 3 --duration-seconds 30 --expected-rx 50 --payload-bytes 60` |
| Result | Pass: 3/3 role-cycle recovery runs reached 75 board-side RX packets with 0 gaps and 0 faults |
| Aggregate summary | `firmware/prototype0/fg23/results/20260807-openref-autorole-recovery-summary.json` |
| Bench restore | Normal non-AutoTX/non-AutoRX/non-AutoRole hook image rebuilt and flashed back to both boards after evidence capture; RAILtest smoke passed |
| Limitation | This validates role idle/restart recovery only; later E0-06 evidence covers malformed packet, queue saturation, forced reset, and memory-watermark checks |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-recovery-precheck-result.md` |

## OpenRef Malformed RX Recovery Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Command | `python tools\openref_malformed_rx_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --malformed-packets 10 --recovery-packets 25 --payload-bytes 60 --command-delay-seconds 0.20 --tx-interval-seconds 0.35 --summary-json firmware\prototype0\fg23\results\20260807-openref-malformed-rx-com8-summary.json` |
| Result | Pass: 10 malformed frames produced 10 parser faults; subsequent 25 valid recovery frames reached RX sequence 25 with 0 gaps and fault counter retained at 10 |
| Aggregate summary | `firmware/prototype0/fg23/results/20260807-openref-malformed-rx-com8-summary.json` |
| Limitation | This validates malformed packet parsing/recovery only; later E0-06 evidence covers queue saturation, forced reset, and memory-watermark checks |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-malformed-rx-result.md` |

## OpenRef Queue Pressure Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Command | `python tools\openref_queue_pressure_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 50 --payload-bytes 60 --command-delay-seconds 0.12 --tx-interval-seconds 0.20 --summary-json firmware\prototype0\fg23\results\20260807-openref-queue-pressure-com8-summary.json` |
| Result | Pass: 50 valid frames reached RX sequence 50 with 0 gaps, 0 faults, `RxFifoFull:0`, `RxOverflow:0`, `NoRxBuffer:0`, and `FrameErrors:0` |
| Aggregate summary | `firmware/prototype0/fg23/results/20260807-openref-queue-pressure-com8-summary.json` |
| Limitation | This validates controlled queue pressure only; a destructive saturation mode still needs a faster sequenced TX source |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-queue-pressure-result.md` |

## OpenRef Forced Reset Recovery Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Command | `python tools\openref_forced_reset_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 50 --payload-bytes 60 --command-delay-seconds 0.15 --tx-interval-seconds 0.25 --reset-settle-seconds 3.0 --summary-json firmware\prototype0\fg23\results\20260807-openref-forced-reset-com8-summary.json` |
| Result | Pass: pre-reset 50/50 and post-reset 50/50, both with 0 gaps, 0 faults, and post-reset RX overflow/buffer counters all zero |
| Aggregate summary | `firmware/prototype0/fg23/results/20260807-openref-forced-reset-com8-summary.json` |
| Limitation | Reset is manually commanded by RAILtest CLI; product firmware still needs final watchdog/reset policy |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-forced-reset-result.md` |

## RAILtest RX Overflow Reset-Recovery Precheck

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Commands | COM8 RX: `python tools\railtest_rx_overflow_recovery_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --overflow-delay-us 100000 --stress-packets 100 --stress-tx-delay-ms 1 --recovery-packets 25 --payload-bytes 60 --summary-json firmware\prototype0\fg23\results\20260808-railtest-rx-overflow-reset-recovery-com8-summary.json`; COM10 RX: `python tools\railtest_rx_overflow_recovery_probe.py --rx-port COM10 --tx-port COM8 --rf-path 0 --overflow-delay-us 100000 --stress-packets 100 --stress-tx-delay-ms 1 --recovery-packets 25 --payload-bytes 60 --summary-json firmware\prototype0\fg23\results\20260808-railtest-rx-overflow-reset-recovery-com10-summary.json` |
| Result | Pass with reset recovery in both directions: each RX board observed `RxOverflow:1`, both boards were reset, then each recovery run delivered 25/25 packets with delivery ratio 1.0 and 0 CRC drops |
| Limitation | No-reset recovery was attempted first and failed on the vendor RAILtest app; product firmware still needs an explicit RX-overflow recovery policy |
| Durable summary | `firmware/prototype0/fg23/20260808-railtest-rx-overflow-reset-recovery-result.md` |

## OpenRef Memory Watermark Precheck

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Build command | `powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`; then `cmake --workflow --preset project` |
| Command | `python tools\openref_memory_watermark_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 50 --payload-bytes 60 --command-delay-seconds 0.15 --tx-interval-seconds 0.25 --summary-json firmware\prototype0\fg23\results\20260807-openref-memory-watermark-com8-summary.json` |
| Result | Pass: OpenRef state footprint stayed 24 bytes before/after traffic; max packet scratch stayed 273 bytes; post-run RX reached 50 with 0 gaps, 0 faults, and RX overflow/buffer counters all zero |
| Aggregate summary | `firmware/prototype0/fg23/results/20260807-openref-memory-watermark-com8-summary.json` |
| Limitation | Fixed-footprint precheck for current OpenRef runtime only; not a general heap profiler for future product firmware |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-memory-watermark-result.md` |

## OpenRef Audio Loopback Analysis Plan

| Item | Value |
|---|---|
| Date | 2026-08-07 |
| Analyzer command | `python tools\analyze_audio_loopback.py firmware\prototype0\fg23\results\YYYYMMDD-e0-07-audio-loopback.csv --expected-samples 10 --target-latency-ms 120 --max-latency-ms 180 --json firmware\prototype0\fg23\results\YYYYMMDD-e0-07-audio-loopback-summary.json` |
| Required events | `impulse`, `capture_frame`, `packet_queue`, `tx_start`, `rx_done`, `playback_output` |
| External status | Requires audio capture/playback fixture and firmware markers before E0-07 can be completed |
| Durable summary | `firmware/prototype0/fg23/20260807-openref-audio-loopback-analysis-plan.md` |

## RAILtest Antenna-Attached Smoke Check

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| RX board | COM8 / SEGGER `440320955` |
| TX board | COM10 / SEGGER `440320878` |
| RF path | 0 |
| Command | `python tools\railtest_pair_smoke.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 20 --output-dir firmware\prototype0\fg23\results` |
| Result | Pass: COM10 reported `transmitted:20`; COM8 logged 20 `rxPacket` events and final status `RxCount:20`, `RxCrcErrDrop:0`, `FrameErrors:0`, `RxOverflow:0` |
| Durable summary | `firmware/prototype0/fg23/20260808-railtest-antenna-smoke-result.md` |

## RAILtest Bidirectional Retention Check

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Command | `python tools\railtest_bidirectional_retention.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 200 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 12 --output-root firmware\prototype0\fg23\results\retention-packet-run --summary-json firmware\prototype0\fg23\results\20260808-railtest-bidirectional-retention-summary.json` |
| Result | Pass: COM10-to-COM8 and COM8-to-COM10 each delivered 200/200 packets with delivery ratio 1.0, zero TX failed packets, and zero RX CRC drops |
| Durable summary | `firmware/prototype0/fg23/20260808-railtest-bidirectional-retention-result.md`; aggregate JSON `firmware/prototype0/fg23/results/20260808-railtest-bidirectional-retention-summary.json` |
| Limitation | Same-bench RF path 0 retention check only; does not replace E0-02 one-hour OpenRef runtime evidence or E0-05 controlled attenuation evidence |

## RAILtest 1000-Packet Antenna Retention Check

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Harness correction | `tools/railtest_pair_smoke.py` now scales the post-TX wait to at least `packets * tx_delay_ms + 5 s`, preventing long packet checks from ending before RAILtest emits final `txEnd` counters |
| Initial 1000-packet attempt | Failed as a harness-timeout artifact: both directions stopped before the final `txEnd` marker, with COM10-to-COM8 at 880 RX packets and COM8-to-COM10 at 871 RX packets, zero CRC drops |
| Retest command | `python tools\railtest_bidirectional_retention.py --rx-port COM8 --tx-port COM10 --rf-path 0 --packets 1000 --payload-bytes 60 --tx-delay-ms 20 --settle-seconds 18 --output-root firmware\prototype0\fg23\results\retention-packet-run-1000 --summary-json firmware\prototype0\fg23\results\20260808-railtest-bidirectional-retention-1000-summary.json` |
| Retest result | Pass: COM10-to-COM8 and COM8-to-COM10 each delivered 1000/1000 packets with delivery ratio 1.0, zero TX failed packets, zero RX CRC drops, zero RX overflow, and final `txStatus:Complete` |
| Durable outputs | Aggregate JSON `firmware/prototype0/fg23/results/20260808-railtest-bidirectional-retention-1000-summary.json`; direction logs under `firmware/prototype0/fg23/results/retention-packet-run-1000` |
| Limitation | Stronger same-bench antenna-retention evidence only; this still does not replace E0-05 controlled attenuation or repeatable shielding evidence |

## Prototype 0 Gate Audit Workflow

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Command | `python tools\audit_prototype0_gates.py --json firmware\prototype0\fg23\results\20260808-prototype0-gate-audit.json --markdown firmware\prototype0\fg23\results\20260808-prototype0-gate-audit.md --mermaid firmware\prototype0\fg23\results\20260808-prototype0-gate-audit.mmd` |
| Result | Pass: audit reports 4 passed gates, 1 partial gate, 2 blocked gates, and 0 evidence problems |
| Retention validation | E0-01 aggregate retention JSON is direction/counter validated: exactly two passing directions, both boards used as TX and RX, requested/transmitted/RX counters match, and TX failures/CRC drops are zero |
| Fixture tracking | Audit now reports readiness state plus latest fixture runner report state for E0-03, E0-05, and E0-07. Current readiness state is `ready` for all three, and current runner-report state is `missing-inputs` because the required physical capture files have not been produced yet. |
| Durable outputs | `firmware/prototype0/fg23/results/20260808-prototype0-gate-audit.json`, `firmware/prototype0/fg23/results/20260808-prototype0-gate-audit.md`, `firmware/prototype0/fg23/results/20260808-prototype0-gate-audit.mmd` |

## Prototype 0 Status Harness

| Item | Value |
|---|---|
| Date | 2026-08-08 |
| Command | `python tools\prototype0_status_run.py --pytest --power-check --packet-smoke --packet-bidirectional --json firmware\prototype0\fg23\results\20260808-prototype0-status-run.json --markdown firmware\prototype0\fg23\results\20260808-prototype0-status-run.md --mermaid firmware\prototype0\fg23\results\20260808-prototype0-status-run.mmd --bench-checklist firmware\prototype0\fg23\results\20260808-prototype0-fixture-bench-checklist.md` |
| Purpose | Single repeatable harness for audit, fixture readiness discovery/dry-runs, optional simulator/tools tests, low-impact board power sanity checks, and short RF path 0 packet smoke in one or both directions |
| Result | Pass: 4 passed gates, 1 partial gate, 2 blocked gates, 0 evidence problems, 196 simulator/tools tests passed, COM8 reported 10.0 dBm, COM10 reported 14.0 dBm, and bidirectional RF path 0 packet smoke passed. COM10-to-COM8 and COM8-to-COM10 each produced 20 RX packet lines, `RxCount:20`, `RxCrcErrDrop:0`, `RxOverflow:0`, `transmitted:20`, and `UserTxStarted:20` |
| External action summary | Status output includes a compact table for E0-03, E0-05, and E0-07 blockers, readiness state, fixture run-report state, fixture-promotion failure reason, and next command |
| Fixture action plan | Status Markdown/JSON now includes a normalized prepare/fill/dry-run/execute command plan for each incomplete fixture gate; prepare commands use dated `*-readiness-template.json` paths, and the compact external-action `next_command` points at the concrete filled-readiness command instead of a `YYYYMMDD` template command |
| Fixture input inventory | Status Markdown/JSON now includes `fixture_input_inventory`, derived from live fixture dry-runs, listing present and missing physical capture inputs per gate plus the expected analyzer summary output |
| Fixture input provenance rollup | `fixture_input_inventory` now carries SHA-256, byte count, and modification-time records for present inputs, `external_blocker_summary.present_artifacts_by_gate` rolls those records up by gate, and Status Markdown renders a `Fixture Artifact Provenance` table whenever a physical fixture input is already present |
| Fixture readiness provenance | Status Markdown now renders a `Fixture Readiness Provenance` table with SHA-256, byte count, and modification-time records for filled E0-03/E0-05/E0-07 readiness files, matching the `readiness_artifact` records stored in fixture run reports |
| Packet-smoke log provenance | Status packet-smoke evidence now records SHA-256, byte count, and modification-time artifact records for each RX/TX log, and Status Markdown renders those records next to each packet-smoke direction |
| Power-check response provenance | Status board power-check entries now include byte count and SHA-256 fingerprint of the raw `getPower` serial response, so the parsed COM8/COM10 dBm values are tied to exact board output |
| Fixture non-closure guardrails | Status Markdown/JSON now includes `fixture_non_closure_guardrails`, explicitly recording the gate-closing evidence required for E0-03/E0-05/E0-07 and the supporting prechecks that must not close those gates. E0-05 baseline delivery, TX-power sweeps, RSSI tone checks, and RF path 1 no-tone behavior remain non-closing until a controlled attenuated or repeatably shielded step is measured |
| Audit next actions | Audit `Next Actions` for E0-03/E0-05/E0-07 now use concrete dated template/check/fill/dry-run/run commands, including the fixture fill step, so the embedded audit table matches the copyable status workflow |
| Fixture command source | Audit and status now share concrete fixture command definitions through `tools/prototype0_fixture_actions.py`, preventing the audit table, external-action summary, fixture action plan, and bench checklist from drifting apart |
| Fixture command coverage | Shared fixture-action tests execute the published template/fill/check/dry-run/run-report commands in a temporary workspace, verify they produce ready metadata plus a v1 missing-inputs run report before stopping at absent physical capture inputs, then inject synthetic analyzer inputs and verify the same run-report commands can produce passing v1 reports. Audit coverage feeds those runner-produced passing reports back through the gate audit and verifies E0-03, E0-05, and E0-07 promote only from that checked fixture evidence path |
| Fixture readiness preflight | Filled v1 readiness metadata now exists for E0-03, E0-05, and E0-07. The fixture runner has written v1 `missing-inputs` reports for each gate. Current absent capture artifacts are `20260808-e0-03-scheduled-tx-gpio.csv`, `20260808-e0-05-step-01-30db.json`, and `20260808-e0-07-audio-loopback.csv`; E0-05 baseline `20260808-e0-05-step-00-baseline.json` is now present |
| External-blocker classification | External-action, fixture-action-plan, and bench-checklist JSON entries now mark remaining physical bench evidence as `external_blocker:true` with `blocker_type:"external-fixture"`; `external_blocker_summary.only_external_blockers` is `true` for the current run |
| External-blocker missing-input rollup | `external_blocker_summary` now carries the exact missing physical input files, per-gate missing/present inputs, and expected analyzer summary outputs when filled readiness metadata exists, so the top-level JSON answers what remains without parsing the fixture inventory table |
| Completion audit | `completion_audit` classifies E0-01/E0-02/E0-04/E0-06 as `proved`, E0-03/E0-05/E0-07 as `external`, `not_proved_gates` as empty, and `all_remaining_work_external:true` |
| Completion diagram | Status `--mermaid` output now renders the same proved/external/not-proved classification plus a completion summary node |
| Status output manifest | When `--json` is used, the status harness writes a sibling `*-artifacts.json` manifest with SHA-256, byte count, and modification-time records for the JSON, Markdown, Mermaid, and bench-checklist outputs requested in the same run |
| Fixture bench checklist | Status Markdown/JSON and `20260808-prototype0-fixture-bench-checklist.md` now include instrument, setup, capture artifact, minimum evidence, pass criteria, and capture-template/template/fill/dry-run/execute commands for E0-03/E0-05/E0-07; verify/execute commands use the same concrete readiness path generated by the fill command |
| Fixture capture templates | `tools/prototype0_fixture_capture_templates.py` writes non-passing example capture-file shapes under `firmware/prototype0/fg23/templates/fixture-captures`: E0-03 edge-list GPIO CSV, E0-05 baseline/attenuated packet-summary JSON skeletons, E0-07 event-timing CSV, and `capture-template-manifest.json`. Status JSON/Markdown now validates that manifest and each template file against repository constants. These files document accepted shape only and cannot close fixture gates without real measured data |
| Fixture capture template determinism | Capture templates are now written with LF line endings on every host, so manifest byte counts and status byte checks match on Windows and POSIX without hiding content drift behind newline normalization |
| Fixture readiness schema | Fixture readiness templates and filled metadata now include `schema:"prototype0-fixture-readiness-v1"`; the checker rejects schema-less or mismatched readiness files so old hand-written metadata cannot accidentally become current evidence |
| Fixture gate closure | Audit now promotes an external-fixture gate from partial/blocked to passed only when the latest run report uses `schema:"prototype0-fixture-run-report-v1"`, includes `generated_at`/`root`, matches the gate, has `status:"passed"`, `pass:true`, no failures, points at valid readiness metadata whose analyzer inputs/output match the run report, and points at an existing summary JSON that reports pass |
| Packet-smoke validation | The harness now validates parsed RX/TX log metrics against the requested packet count and requires zero CRC drops/overflow for every requested direction; bidirectional runs keep each direction's RX/TX logs in separate timestamped directories |
| Fixture-runner validation | Fixture analyzer execution now requires both a zero analyzer exit and a generated summary JSON reporting `pass:true`/`passed:true`; missing, invalid, or failed summaries fail the run report |
| Fixture-runner report schema | Fixture runner reports now include `schema:"prototype0-fixture-run-report-v1"`, `generated_at`, and `root` so saved success and failure reports remain traceable audit artifacts |
| Fixture artifact provenance | Fixture runner reports now include SHA-256, byte count, and modification-time artifact records for the readiness file, every input, and the analyzer summary JSON. Audit promotion rejects passed fixture reports without those provenance records or with recorded byte counts/hashes that no longer match the current files, tying closure evidence to exact capture bytes. Current missing-input reports have been refreshed with artifact records; E0-05 baseline SHA-256 is `1c5a1e395cbe10e5eeea0a27745c3f8e8e1a14ee89f663194f7c16a861234957` |
| Fixture input contracts | Fixture runner now rejects malformed E0-03 GPIO CSVs, E0-05 packet-summary JSON files, and E0-07 event CSVs before invoking analyzers, so bad exports produce immediate `invalid-inputs` run reports |
| Expected incomplete state | Ready E0-03/E0-05/E0-07 readiness files with `missing-inputs` fixture reports are reported as external-input work, not as harness failures |
| Readiness reporting | If only template/example readiness files exist, the fixture dry-run table shows the latest manifest readiness path and not-ready status instead of leaving the readiness cell blank |
| Durable outputs | `firmware/prototype0/fg23/results/20260808-prototype0-status-run.json`, `firmware/prototype0/fg23/results/20260808-prototype0-status-run.md`, `firmware/prototype0/fg23/results/20260808-prototype0-status-run.mmd` |

## Vendor-Derived Files

Do not copy files from the SDK into this repository until this table is filled
for each file.

| Repository file | Vendor source file | SDK version | License | Modifications |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD |

## Open Questions

- Which Silicon Labs API exposes the required local timestamp for scheduled TX? Current precheck uses `RAIL_GetTime()` plus `RAIL_EVENT_TX_STARTED` / `txStartTime`; external GPIO capture is still required for final E0-03.
- Which API exposes RSSI, LQI, CRC status, and packet length in receive metadata?
- What PHY profile best approximates the simulator's 500 kbps baseline?
- What GPIOs are easiest to use as timing markers on the FG23-DK2600A? Current bench plan uses `PB3` queue and `PB2` TX-start, with optional `PB0` build and `PA5` TX-done.
