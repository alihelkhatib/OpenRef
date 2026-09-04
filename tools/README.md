# OpenRef Tools

Small repository-owned scripts for analysis, validation, and prototype evidence.

Tools should avoid machine-specific paths and should be runnable from a clean
checkout with documented dependencies.

## RT595 Release Bundle

`assemble_rt595_release_bundle.py` creates a self-contained handoff directory
from a bootstrap binary, slot-linked application, signed slot package, canonical
flash layout and reports, public trust anchor, and release provenance. It
re-verifies the signature and enforces slot, address, version, key-ID, payload
hash, vector-table, layout, and provenance consistency. Assembly refuses to
overwrite or merge an existing directory.

The command deliberately has no private-key argument. Signing happens earlier
with `package_rt595_signed_slot.py`; only the public key enters the bundle. Run
the `assemble` command and then independently run `verify BUNDLE_DIRECTORY`.
`bundle.json` records `release_ready: false` unless `--reviewed-evidence`
supplies a strict `openref.rt595.release-review.v1` approval from an identified
independent reviewer, timestamped and bound to the exact subject hashes, slot,
version, and key ID. A passing build or provenance inventory alone cannot
promote readiness.

## Serial Capture

List serial ports:

```bash
python tools/capture_serial.py --list
```

Capture a board log:

```bash
python tools/capture_serial.py \
  --port COM7 \
  --baud 115200 \
  --duration-seconds 120 \
  --output firmware/prototype0/fg23/results/YYYYMMDD-node-1.log
```

Requires `pyserial`:

```bash
python -m pip install pyserial
```

Run the two-board FG23 RAILtest smoke test:

```bash
python tools/railtest_smoke.py
```

The smoke test auto-detects SEGGER/J-Link USB serial ports, sends `help` to
each RAILtest board, writes logs under `firmware/prototype0/fg23/results`, and
fails if the expected RAILtest command list is not returned.

Run a short two-board RAILtest packet exchange:

```bash
python tools/railtest_pair_smoke.py
```

By default, the first detected SEGGER serial port is the receiver and the second
is the transmitter. Override this with `--rx-port COMx --tx-port COMy` if the
bench wiring requires fixed roles. Use `--rf-path 0` or `--rf-path 1` to force
a specific radio path before testing.

Probe RF energy with a transmit tone and receiver RSSI reading:

```bash
python tools/railtest_rssi_probe.py --rf-path 0
```

This is useful when serial and TX completion work, but the receiver reports no
sync detects or received packets.

Use `--expect no-tone` for expected-negative path checks, for example to confirm
that an unused RF path stays near the noise floor:

```bash
python tools/railtest_rssi_probe.py --rx-port COM8 --tx-port COM10 --rf-path 1 --expect no-tone --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-rssi-com8-rx-com10-tx-rf1-summary.json
```

For durable Prototype 0 evidence, run each direction with a summary file:

```bash
python tools/railtest_rssi_probe.py --rx-port COM8 --tx-port COM10 --rf-path 0 --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-rssi-com8-rx-com10-tx-rf0-summary.json
python tools/railtest_rssi_probe.py --rx-port COM10 --tx-port COM8 --rf-path 0 --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-rssi-com10-rx-com8-tx-rf0-summary.json
```

Run a counted packet check and write a JSON summary:

```bash
python tools/railtest_packet_run.py \
  --packets 100 \
  --payload-bytes 60 \
  --tx-delay-ms 20 \
  --settle-seconds 30 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-packet-run.json
```

This still uses the vendor RAILtest application. It is a bench precheck before
the OpenRef-owned E0-02 packet-pair firmware.

Run a medium bidirectional packet-retention check with separate logs and an
aggregate JSON result:

```bash
python tools/railtest_bidirectional_retention.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --packets 200 \
  --payload-bytes 60 \
  --tx-delay-ms 20 \
  --settle-seconds 12 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-bidirectional-retention-summary.json
```

This runs COM10-to-COM8 and COM8-to-COM10 sequentially, keeps each direction's
logs in its own output directory, and fails if either direction does not report
the requested transmit count, receive count, zero TX failures, and zero CRC
drops.
For long runs with `--tx-delay-ms`, the underlying pair runner waits at least
`packets * tx_delay_ms + 5 s` before reading final RAILtest counters, so a valid
long run is not cut short by a too-small manual settle value.

Send actual OpenRef prototype packets through the RAILtest TX FIFO and decode
them from the receiver log:

```bash
python tools/railtest_openref_packet_run.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --packets 50 \
  --payload-bytes 60 \
  --interval-seconds 0.35 \
  --command-delay-seconds 0.15 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-railtest-summary.json
```

This sets RAIL fixed-length mode for the OpenRef frame size before transmitting.
It validates the OpenRef wire format over the real RF link, while still using
RAILtest as the board-side radio shell.

Validate an opt-in board-generated OpenRef AutoTX image:

```bash
python tools/railtest_openref_autotx_rx.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --expected-packets 10 \
  --duration-seconds 8 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-autotx-summary.json
```

This assumes the TX board has been flashed from an overlay installed with
`tools/install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoTx`.

Capture board-side AutoRX counters:

```bash
python tools/openref_autorx_marker_run.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --duration-seconds 300 \
  --expected-rx 700 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-autorx-summary.json
```

This assumes the RX board was flashed with `-EnableAutoRx` and the TX board was
flashed with `-EnableAutoTx`.

Run the same-image AutoRole test:

```bash
python tools/openref_autorole_run.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --duration-seconds 300 \
  --expected-rx 700 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-autorole-summary.json
```

This assumes both boards were flashed from an overlay installed with
`tools/install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole`. The
runner resolves the `openref_app_role` symbol from the generated ELF, then uses
RAILtest `setmemw` to select RX and TX roles at runtime. Use
`--payload-bytes` to set the OpenRef payload length when the firmware image
exports `openref_app_payload_bytes`.

Run an OpenRef runtime payload capacity sweep:

```bash
python tools/openref_autorole_capacity_sweep.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --payloads 16 60 120 200 \
  --duration-seconds 60 \
  --expected-rx 120
```

This assumes both boards are running the same `-EnableAutoRole` image. The
sweep changes payload length and roles at runtime, then writes per-payload JSON
summaries plus an aggregate summary under `firmware/prototype0/fg23/results`.

Run OpenRef role-cycle recovery checks:

```bash
python tools/openref_autorole_recovery_probe.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --cycles 3 \
  --duration-seconds 30 \
  --expected-rx 50 \
  --payload-bytes 60
```

This repeatedly starts RX/TX roles, verifies board-side OpenRef counters, then
returns both boards to the idle role before the next cycle.

Run OpenRef malformed-packet RX recovery checks:

```bash
python tools/openref_malformed_rx_probe.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --malformed-packets 10 \
  --recovery-packets 25 \
  --payload-bytes 60 \
  --command-delay-seconds 0.20 \
  --tx-interval-seconds 0.35 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-malformed-rx-summary.json
```

This assumes COM8 is running the same `-EnableAutoRole` image and COM10 is
running the normal RAILtest/OpenRef hook image. The probe injects bad OpenRef
magic bytes, verifies `Status:ParseFail` markers, then sends valid packets to
confirm RX recovery with no sequence gaps.

Run OpenRef queue-pressure checks:

```bash
python tools/openref_queue_pressure_probe.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --packets 50 \
  --payload-bytes 60 \
  --command-delay-seconds 0.12 \
  --tx-interval-seconds 0.20 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-queue-pressure-summary.json
```

Run OpenRef forced-reset recovery checks:

```bash
python tools/openref_forced_reset_probe.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --packets 50 \
  --payload-bytes 60 \
  --command-delay-seconds 0.15 \
  --tx-interval-seconds 0.25 \
  --reset-settle-seconds 3.0 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-forced-reset-summary.json
```

Run a vendor RX-overflow reset-recovery check:

```bash
python tools/railtest_rx_overflow_recovery_probe.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --overflow-delay-us 100000 \
  --stress-packets 100 \
  --stress-tx-delay-ms 1 \
  --recovery-packets 25 \
  --payload-bytes 60 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-rx-overflow-reset-recovery-summary.json
```

By default this probe resets both boards after the induced overflow, then
requires a normal packet exchange to pass. Use `--no-reset-after-overflow` only
when explicitly checking no-reset recovery behavior.

Run OpenRef memory-watermark checks:

```bash
python tools/openref_memory_watermark_probe.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --packets 50 \
  --payload-bytes 60 \
  --command-delay-seconds 0.15 \
  --tx-interval-seconds 0.25 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-memory-watermark-summary.json
```

Run the OpenRef scheduled-TX SDK timestamp probe:

```bash
python tools/openref_scheduled_tx_run.py \
  --port COM8 \
  --rf-path 0 \
  --attempts 100 \
  --payload-bytes 60 \
  --timeout-seconds 20 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-openref-scheduled-tx-summary.json
```

This assumes the board is running the `-EnableAutoRole` image. The runner sets
AutoRole role `3`, captures `openrefSchedTx` markers, and computes launch-error
statistics from the RAIL TX-start timestamp.

Build an opt-in scheduled-TX GPIO marker image for external E0-03 timing
capture:

```powershell
powershell -ExecutionPolicy Bypass -File tools\install_openref_fg23_overlay.ps1 -InstallAppShim -EnableAutoRole -BuildMarker B0 -QueueMarker B3 -StartMarker B2 -DoneMarker A5
```

On BRD2600A rev A03, the preferred minimum analyzer wiring is `PB3` for the
scheduled-TX queue marker and `PB2` for the TX-start marker. `PB0` and `PA5`
can be added for packet-built and TX-done markers when four capture channels
are available.

Analyze the exported E0-03 GPIO capture:

```bash
python tools/analyze_scheduled_tx_gpio.py \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-03-scheduled-tx-gpio.csv \
  --queue-channel PB3 \
  --start-channel PB2 \
  --expected-samples 100 \
  --fail-on-unpaired-edges \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-03-scheduled-tx-gpio-summary.json
```

Convert a RAILtest RX log to the OpenRef analyzer CSV shape:

```bash
python tools/railtest_to_packet_csv.py \
  firmware/prototype0/fg23/results/YYYYMMDD-railtest-pair-rx.log \
  --output firmware/prototype0/fg23/results/YYYYMMDD-railtest-packet-run.csv
```

Probe the scheduled TX API path:

```bash
python tools/railtest_scheduled_tx_probe.py \
  --port COM8 \
  --count 10 \
  --relative-delay-us 50000 \
  --spacing-seconds 0.25 \
  --rf-path 0
```

Analyze E0-05 controlled-attenuation packet summaries:

```bash
python tools/analyze_attenuation_sweep.py \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-05-step-00-baseline.json \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-05-step-01-shielded.json \
  --labels baseline shielded \
  --min-steps 2 \
  --min-packet-error-rate 0.01 \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-05-attenuation-summary.json
```

Run a software-controlled TX-power link-margin precheck:

```bash
python tools/railtest_tx_power_sweep.py \
  --rx-port COM8 \
  --tx-port COM10 \
  --rf-path 0 \
  --powers-dbm 14 0 -10 \
  --restore-power-dbm 14 \
  --packets 50 \
  --payload-bytes 60 \
  --tx-delay-ms 20 \
  --settle-seconds 8 \
  --summary-json firmware/prototype0/fg23/results/YYYYMMDD-railtest-tx-power-sweep-summary.json
```

Analyze E0-07 audio loopback timing captures:

```bash
python tools/analyze_audio_loopback.py \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-07-audio-loopback.csv \
  --expected-samples 10 \
  --target-latency-ms 120 \
  --max-latency-ms 180 \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-07-audio-loopback-summary.json
```

Audit Prototype 0 gate evidence:

```bash
python tools/audit_prototype0_gates.py \
  --json firmware/prototype0/fg23/results/YYYYMMDD-prototype0-gate-audit.json \
  --markdown firmware/prototype0/fg23/results/YYYYMMDD-prototype0-gate-audit.md \
  --mermaid firmware/prototype0/fg23/results/YYYYMMDD-prototype0-gate-audit.mmd
```

Run the combined Prototype 0 status harness:

```bash
python tools/prototype0_status_run.py \
  --pytest \
  --power-check \
  --packet-smoke \
  --packet-bidirectional \
  --json firmware/prototype0/fg23/results/YYYYMMDD-prototype0-status-run.json \
  --markdown firmware/prototype0/fg23/results/YYYYMMDD-prototype0-status-run.md \
  --mermaid firmware/prototype0/fg23/results/YYYYMMDD-prototype0-status-run.mmd \
  --bench-checklist firmware/prototype0/fg23/results/YYYYMMDD-prototype0-fixture-bench-checklist.md
```

The status harness runs the gate audit, discovers live E0-03/E0-05/E0-07
readiness files, dry-runs any ready fixture analyzers, and optionally runs the
simulator/tools test suite. With `--power-check`, it also queries RAILtest
`getPower` on COM8 and COM10 by default; use repeatable `--power-port COMx`
arguments to override those ports. Board power-check entries include the parsed
dBm value plus a byte count and SHA-256 fingerprint of the raw serial response,
so the status JSON/Markdown can prove exactly what response was parsed. With
`--packet-smoke`, it runs a short COM10-to-COM8 RF path 0 packet smoke by
default; use `--packet-rx-port`,
`--packet-tx-port`, `--packet-rf-path`, and `--packet-count` to override it.
Add `--packet-bidirectional` to run the reversed direction in the same harness
run. Each direction writes logs under a timestamped `status-packet-smoke`
subdirectory so the second run does not overwrite the first. The packet-smoke
section parses the generated RX/TX logs and reports RX packet line count, final
`RxCount`, CRC drops, overflow count, TX transmitted count, and TX started
count. A requested packet smoke fails the harness if any requested direction's
parsed metrics do not match the requested packet count or if CRC drops/overflow
are nonzero, even when the smoke subprocess exits successfully. The same
packet-smoke evidence now records SHA-256, byte count, and modification-time
artifact records for both RX and TX logs, and Status Markdown renders those
records next to each packet-smoke direction.
Missing live readiness files are reported as expected external-input work, not
as a harness failure. Evidence problems, test failures, requested power-check
failures, and requested packet-smoke failures still make the harness fail.
When no live readiness file is discoverable because only templates/examples are
present, the dry-run table still reports the latest manifest readiness path and
its audit failures so the next operator step is visible.
The status Markdown/JSON also includes an `External Actions` section derived
from the audit's incomplete gates, so E0-03/E0-05/E0-07 blockers, readiness
state, run-report state, fixture-promotion failure reason, and next command stay
visible in one compact table.
External-action, fixture-action-plan, and bench-checklist JSON entries also set
`external_blocker: true` and `blocker_type: "external-fixture"` for incomplete
gates whose remaining work requires physical bench evidence.
The `external_blocker_summary` JSON field and Markdown section roll those fields
up into `only_external_blockers`, `incomplete_gates`, `external_blocked_gates`,
`unclassified_incomplete_gates`, and `evidence_problem_count`. When filled
readiness files exist, the same summary includes `missing_input_count`,
`all_missing_inputs`, `missing_inputs_by_gate`, `present_inputs_by_gate`,
`present_artifacts_by_gate`, and `summary_outputs_by_gate` so the remaining
physical artifact list and already-captured input hashes are available without
parsing the later fixture inventory table.
The `completion_audit` JSON field and Markdown section classify every gate as
`proved`, `external`, or `not-proved`; the current Prototype 0 report is not
complete because external fixture gates remain, but `all_remaining_work_external`
is true and `not_proved_gates` is empty.
The status harness `--mermaid` output uses the same completion classification,
so the `.mmd` graph shows proved gates, external-fixture gates, any not-proved
gates, and the final completion summary node.
When `--json` is used, the status harness also writes a sibling
`*-artifacts.json` manifest with SHA-256, byte count, and modification-time
records for every requested status output file (`--json`, `--markdown`,
`--mermaid`, and `--bench-checklist`). This makes the status report set itself
verifiable after handoff.
The `Fixture Action Plan` section and `fixture_action_plan` JSON field normalize
the same incomplete-gate data into bench steps: prepare the readiness template,
fill readiness metadata with concrete capture paths/settings, dry-run the
analyzer command, then execute the fixture run report after the physical capture
exists. The generated verify and execute commands use the same concrete
readiness path emitted by the fill command, so a copied command block does not
mix dated readiness files with `YYYYMMDD` placeholders.
Prepare/template commands in the status action plan use dated
`*-readiness-template.json` paths for the same reason.
The compact `External Actions` table also exposes a concrete `next_command`
from that plan, so the top-level status summary points at the filled readiness
command instead of the placeholder manifest template command.
Audit and status share those concrete fixture command paths through
`tools/prototype0_fixture_actions.py`, keeping the embedded audit table,
external-action summary, fixture action plan, and standalone bench checklist in
sync.
The shared fixture action tests execute the template, fill, check, dry-run, and
run-report commands in a temporary workspace, proving the published command
strings produce ready metadata, write a v1 fixture run report, and stop at
missing physical capture inputs rather than failing from quoting or path drift.
The same test injects synthetic analyzer inputs and reruns the published
run-report commands, proving the commands can also produce passing v1 run
reports once real fixture captures exist.
The audit tests then feed those runner-produced passing reports back through
the gate audit and prove E0-03, E0-05, and E0-07 are promoted only from that
schema-checked fixture evidence path.
The `Fixture Bench Checklist` section and optional `--bench-checklist` output
add the required instrument, wiring/setup invariants, capture artifact, minimum
evidence, pass criteria, and a PowerShell command block for each gate: generate
non-passing example capture-file templates, generate the readiness template,
generate a filled readiness file with concrete placeholders, dry-run the
analyzer, then execute the fixture run report after capture.

For JSON evidence marked as pass-required, object summaries must contain
`"pass": true` or `"passed": true`. Aggregate list summaries must be non-empty
and every item in the list must pass. The E0-01 bidirectional retention
aggregate has an additional validator: it must contain exactly two passing
directions, exercise both boards as TX and RX, match requested/transmitted/RX
packet counters, and report zero TX failures and CRC drops.

The audit also verifies that each Markdown evidence document in the manifest is
referenced by the gate-status rollup, defaulting to
`firmware/prototype0/fg23/20260807-prototype0-gate-status.md`. Use
`--rollup-doc` if a future rollup file replaces it. For partial or blocked
gates, the rollup must also represent the blocker terms, so a status document
cannot drop the external-input reason while the manifest still marks the gate
incomplete. Partial or blocked gates include concrete `Next Actions` with the
fixture readiness template/check/fill commands, runner dry-run, and runner
execution command needed before final evidence can be captured.
For E0-03, E0-05, and E0-07, the audit also inspects the newest matching
`results/*-e0-XX-readiness*.json` file and reports `missing`, `not-ready`,
`invalid`, or `ready` plus readiness failures or the resulting analyzer command.
Readiness files must use `schema:"prototype0-fixture-readiness-v1"`; schema-less
or mismatched readiness metadata remains `not-ready` so old hand-written files
cannot accidentally close a current gate.
When readiness is `ready`, the audit derives the analyzer input paths and output
summary path from that command, then reports how many inputs exist and whether
the generated summary JSON exists and passes. The audit also reports the newest
`*-e0-XX-run-report*.json` fixture runner output, so completed fixture analyzer
runs stay visible in the gate table instead of only existing as loose result
files. For external-fixture gates, a latest run report with
`schema:"prototype0-fixture-run-report-v1"`, `generated_at`, `root`, matching
`gate`, `status:"passed"`, `pass:true`, no failures, a valid readiness file
whose analyzer inputs/output match the run report, and an output summary JSON
that exists and reports pass promotes that gate from partial/blocked to passed
in the audit; reports for the wrong gate, missing/invalid readiness, or
failed/stale reports do not close the gate.
The status harness also emits `fixture_input_inventory` in JSON/Markdown. It is
derived from the live fixture dry-runs and lists every required physical input
path as present or missing, plus the expected analyzer summary output. Present
input entries carry SHA-256, byte count, and modification-time provenance, and
Markdown renders `Fixture Readiness Provenance` and `Fixture Artifact
Provenance` tables whenever readiness files or fixture inputs exist. This is the
compact handoff for the remaining bench work.
It also emits `fixture_non_closure_guardrails`, which records the exact evidence
that can close E0-03/E0-05/E0-07 and the prechecks that must remain non-closing
supporting evidence. In particular, E0-05 baseline delivery, TX-power sweeps,
RSSI tone checks, and RF path 1 no-tone behavior do not replace a controlled
attenuated or repeatably shielded step.

Run a fixture analyzer from a filled readiness file:

```bash
python tools/run_prototype0_fixture_analysis.py \
  --readiness firmware/prototype0/fg23/results/YYYYMMDD-e0-07-readiness.json \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-07-run-report.json
```

Write non-passing example capture-file templates for the external fixture gates:

```bash
python tools/prototype0_fixture_capture_templates.py \
  --gate all \
  --output-dir firmware/prototype0/fg23/templates/fixture-captures \
  --json firmware/prototype0/fg23/templates/fixture-captures/capture-template-manifest.json
```

These files document accepted input shape only. They are intentionally
insufficient or placeholder-filled: E0-03 has fewer than 100 paired GPIO samples,
E0-05 has replacement strings where measured packet counters belong, and E0-07
has fewer than 10 complete event chains. They must be replaced with real
physical capture data before running fixture evidence for closure.
The status harness reports `fixture_capture_templates` in JSON/Markdown and
checks the manifest plus every generated template file against the repository
template constants. This support check is provenance for the bench handoff; it
does not promote or fail a gate because these examples are not evidence.
The capture-template writer forces LF line endings so manifest byte counts and
status byte checks are deterministic on Windows and POSIX hosts.

Use `--dry-run` first to verify the exact analyzer command and input paths
without executing the analyzer. The runner fails before execution if required
capture inputs are missing. A real runner execution now also requires the
analyzer to write the expected summary JSON and for that summary to contain
`"pass": true` or `"passed": true`; a zero subprocess exit alone is not enough
to mark fixture evidence as passed. Every fixture runner report includes
`schema:"prototype0-fixture-run-report-v1"`, `generated_at`, and `root` so saved
run reports are traceable audit artifacts even when they fail before analyzer
execution. Runner reports also include SHA-256, byte count, and modification-time
artifact records for the readiness file, every input, and the expected summary JSON. The audit
refuses to promote external fixture gates from passed reports that lack those
artifact records or whose recorded byte counts or hashes do not match the
current files, so final fixture evidence is tied to exact capture bytes. The
runner also performs lightweight input contract checks before
analysis: E0-03 GPIO captures must expose a recognized time column plus
edge-list or PB3/PB2 sampled columns, E0-05 packet summaries must contain
requested/transmitted packet counts at or above the readiness
`packet_count_per_step` plus RX count fields, and E0-07 timing captures must
expose time, frame/id, and event columns. E0-05 readiness derives its analyzer
summary path from the concrete baseline JSON path, so filled metadata does not
write a placeholder-named attenuation summary.

To run or dry-run the newest live readiness file for a gate, use discovery:

```bash
python tools/run_prototype0_fixture_analysis.py --gate E0-03 --dry-run
python tools/run_prototype0_fixture_analysis.py --gate E0-05 --json firmware/prototype0/fg23/results/YYYYMMDD-e0-05-run-report.json
python tools/run_prototype0_fixture_analysis.py --gate E0-07 --dry-run
```

Discovery scans `firmware/prototype0/fg23/results` for the newest
`*-e0-XX-readiness*.json` file and ignores templates, examples, check reports,
and previous run reports.

## Packet-Pair Analyzer

Analyze E0-02 receiver logs:

```bash
python tools/analyze_packet_pair.py \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-02-packet-pair.csv \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-02-summary.json
```

For gate-style verification, pass explicit criteria. The command exits nonzero
when any criterion fails and includes `pass`, `criteria`, and `failures` in the
summary JSON:

```bash
python tools/analyze_packet_pair.py \
  firmware/prototype0/fg23/results/YYYYMMDD-e0-02-packet-pair.csv \
  --min-received 9000 \
  --max-sequence-gaps 0 \
  --max-rx-gap-events 0 \
  --max-fault-events 0 \
  --max-boot-events 1 \
  --max-inter-arrival-us 100000 \
  --json firmware/prototype0/fg23/results/YYYYMMDD-e0-02-summary.json
```

## Fixture Readiness

Generate and validate metadata before running external-fixture gates:

```bash
python tools/prototype0_fixture_readiness.py --gate E0-03 --template --json firmware/prototype0/fg23/results/YYYYMMDD-e0-03-readiness.json
python tools/prototype0_fixture_readiness.py --gate E0-03 --check firmware/prototype0/fg23/results/YYYYMMDD-e0-03-readiness.json
```

Generate a filled readiness file without hand-editing JSON:

```bash
python tools/prototype0_fixture_readiness.py --gate E0-03 --fill \
  --set "instrument=Saleae Logic Pro 8" \
  --set ground_connected=true \
  --set output_csv=firmware/prototype0/fg23/results/20260808-e0-03-gpio.csv \
  --json firmware/prototype0/fg23/results/20260808-e0-03-readiness.json
```

For E0-05, replace the template attenuation step list with one or more concrete
steps:

```bash
python tools/prototype0_fixture_readiness.py --gate E0-05 --fill \
  --set "method=Mini-Circuits VAT-30+ inline attenuator" \
  --set baseline_summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-00-baseline.json \
  --set "physical_setup_note=COM10 SMA cabled through attenuator to shielded receive setup." \
  --attenuated-step "label=30dB,physical_setting=30 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-01-30db.json" \
  --attenuated-step "label=60dB,physical_setting=60 dB inline attenuator,summary_json=firmware/prototype0/fg23/results/20260808-e0-05-step-02-60db.json" \
  --json firmware/prototype0/fg23/results/20260808-e0-05-readiness.json
```

For E0-07, use `--audio-event` when the capture file uses marker names other
than the default labels:

```bash
python tools/prototype0_fixture_readiness.py --gate E0-07 --fill \
  --set "fixture_method=wired DAC output into ADC capture fixture" \
  --set firmware_timing_markers=true \
  --set output_csv=firmware/prototype0/fg23/results/20260808-e0-07-audio.csv \
  --audio-event capture=frame_ready \
  --audio-event playback=audio_out \
  --json firmware/prototype0/fg23/results/20260808-e0-07-readiness.json
```

Supported gates are `E0-03`, `E0-05`, and `E0-07`. The checker fails missing
schema, instrument, wiring, attenuation, event, marker, or setup metadata before
a physical capture can become ambiguous evidence. Generated templates contain
`schema:"prototype0-fixture-readiness-v1"` plus placeholder values and must be
filled with concrete fixture details before `--check` can pass; do not leave
`YYYYMMDD`, `describe`, or generic instrument text in a filled readiness file.
E0-03 and E0-07 fixture captures must point at `.csv` outputs; E0-05 packet
summaries must point at `.json` outputs. E0-03 analyzer flags must be a string
list, E0-05 attenuation labels must be filled and unique, and E0-07 must list
the exact expected marker events once. E0-07 `event_aliases` map analyzer stage
keys to the labels present in the timing CSV, and non-default aliases are
emitted as `--event` analyzer arguments. When a readiness file
passes, the checker includes both an `analysis_command` array and
`analysis_command_text` PowerShell-friendly string for the exact next analyzer
command.

Run tool tests:

```bash
python -B -m pytest -p no:cacheprovider tools/tests --basetemp .pytest-tmp
```

## Prototype 1 readiness inputs

Generate or validate the nine evidence/design inputs that remain open before
Prototype 1 schematic review:

```text
python tools/prototype1_readiness_inputs.py --template --json hardware/prototype1-wearable/readiness-inputs-YYYYMMDD.json
python tools/prototype1_readiness_inputs.py --check --json hardware/prototype1-wearable/readiness-inputs-YYYYMMDD.json
```

An input may be marked `verified` only with a concrete `value`, reviewer,
timezone-qualified timestamp, and at least one current SHA-256-bound evidence
artifact. The checker remains non-passing for `open` inputs and does not treat
vendor estimates as measured OpenRef evidence.
# Release artifact provenance

`create_release_provenance.py` emits a deterministic JSON inventory for an
RT595 release candidate. It binds each ELF, map, configuration, and validation
report to its byte count and SHA-256 digest; records the exact Git HEAD,
tracked-diff digest, porcelain status, and hashes of untracked source files;
and records explicitly supplied toolchain versions. The output always carries
`release_ready: false`: it is an artifact/provenance record, not a substitute
for `audit_mvp_readiness.py` or missing physical evidence.

Example (paths may point into the ignored local SDK build directory):

```powershell
python tools/create_release_provenance.py `
  --output artifacts/local/release/rt595-integrated-provenance.json `
  --artifact firmware_elf=artifacts/local/rt595-sdk/build/openref_rt595_integrated/openref_rt595_integrated_cm33.elf `
  --artifact linker_map=artifacts/local/rt595-sdk/build/openref_rt595_integrated/output.map `
  --artifact flash_layout=firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_flash_layout.json `
  --validation native=passed:artifacts/local/reports/native-tests.txt `
  --tool arm_gnu=14.3.1 --tool mcuxsdk=26.06.00-LTS
```

Validation status is caller-declared and must be bound to a report file. The
generator never infers success from a filename or console text. External file
locations are reduced to basenames to avoid embedding machine-specific paths.
`verify_release_provenance.py` rechecks repository state and all hashes. Supply
the current path for every external record with `--artifact ROLE=PATH` or
`--validation NAME=PATH`; repository-scoped records resolve automatically.
