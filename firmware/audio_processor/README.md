# Audio Processor Firmware

This subtree contains processor-independent audio-path code and target adapters
for the separate OpenRef audio processor selected after the FG23 LC3 benchmark.

## Common

`common/openref_audio_mixer.h/.c` implements a bounded five-source, 16 kHz,
10 ms-block mixer. It uses per-source Q15 gain, immediate limiter attack,
controlled release, saturation defense, and cumulative diagnostics. It performs
no dynamic allocation and has no vendor SDK dependency.

`common/openref_audio_playout.h/.c` owns six independently bounded encoded-audio
queues. It tracks 20 ms sequence numbers, releases each 40-byte half-frame on a
10 ms cadence, rejects duplicate/stale input, and explicitly requests LC3 PLC
for missing or invalid halves. Queue overflow discards old packets; stale audio
is never replayed.

`common/openref_audio_runtime.h/.c` is the target-facing 10 ms execution layer.
It joins microphone encode, local packet assembly, five-source decode/PLC, and
headphone mixing while measuring encode, render, and total processing time. It
flags capture discontinuities and counts any block that exceeds the 8 ms
processing budget. Board adapters provide only codec and monotonic-clock
callbacks and move DMA buffers at the boundary.

## Processor Benchmark

`benchmark/openref_audio_benchmark.h/.c` defines the reproducible promotion
workload: one 16 kHz LC3 encoder, five independent decoders, PLC, five-source
mixing, and an 8 ms processing deadline. See
[`benchmark/README.md`](benchmark/README.md) for the fixed run length, callback
contract, result schema, and result-validation command. Native runs verify the
portable integration only; performance claims require a paced target run.

## Target Direction

The first target adapter will be MIMXRT595-EVK. It will connect:

- digital microphone DMA to the LC3 encoder;
- five LC3 decoders to the common mixer;
- the mixer to codec/headphone DMA; and
- the fixed processor-link frame to an SPI peripheral endpoint.

Target promotion requires the exit tests in
`docs/adr/ADR-0006-prototype-audio-processor-platform.md`.
New board ports should follow the directory and evidence conventions in
[`targets/README.md`](targets/README.md).

## Native Verification

`tools/run_firmware_native_tests.py` compiles and executes the portable network,
link, capture, playout, mixer, integrated-pipeline, runtime, and processor
benchmark C tests. The local
2026-08-14 run used the official Zig 0.16.0 Windows archive with SHA-256
`68659eb5f1e4eb1437a722f1dd889c5a322c9954607f5edcf337bc3684a75a7e`.
The compiler is kept in ignored artifacts and is not installed system-wide.
