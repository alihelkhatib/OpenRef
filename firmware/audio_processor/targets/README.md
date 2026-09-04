# Audio Processor Target Ports

Create one directory per board, named with a stable lowercase board identifier
(for example, `mimxrt595_evk/`). Keep vendor SDK output and generated build
trees out of the portable `common/` and `benchmark/` directories.

A benchmark-capable target port needs to provide:

- one LC3 encoder instance and five independent decoder instances;
- codec callbacks matching `openref_audio_benchmark_hooks_t`, including the
  codec's real packet-loss concealment path;
- a monotonic microsecond clock with enough resolution to enforce the 8 ms
  deadline;
- 10 ms task pacing outside `openref_audio_benchmark_step()`; and
- a serial, file, or debugger export of the complete benchmark result and its
  build, memory-placement, stack, and current-measurement provenance.

The promotion run uses only the portable benchmark's deterministic loss
schedule. Do not inject additional packet loss in a target port: with the
canonical 1,000-block warmup, 180,000-block measurement, and 97-packet period,
the measured result contains exactly 927 PLC calls.

Do not copy or alter the portable workload for a vendor SDK. Adapt SDK codec,
timer, DMA, and output APIs at the target boundary so all candidates execute
the same sources and constants. Document the exact SDK example or project used
to reproduce the build in the board directory.

Follow [`../benchmark/README.md`](../benchmark/README.md) for the fixed workload
and JSON contract. Validate a captured result from the repository root with:

```text
python tools/validate_audio_benchmark_result.py result.json
```

Store raw serial logs, ELF/map files, instrument captures, and local manifests
under `artifacts/local/<date>-<board>-audio-benchmark/`; that tree is ignored.
Commit only a reviewed Markdown conclusion with an external archive hash when
the result is promotion evidence.
