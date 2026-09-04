# Audio Processor Candidate Screening

This directory defines the inexpensive screen performed before buying another
development board. It uses the unchanged vendor-neutral workload in
`../benchmark/`; it does not create reduced candidate-specific benchmarks.

## Evidence ladder

1. Cross-compile the portable workload and record its object footprint.
2. Link the real LC3 implementation with the candidate SDK and record the ELF,
   map, compiler version, flags, and memory placement.
3. Run the canonical paced benchmark on vendor- or borrower-operated hardware.
4. Measure stack high-water and idle, one-talker, and six-talker current.
5. Buy a board only for candidates that survive the preceding screens, unless
   acquiring the board is cheaper than obtaining equivalent vendor support.

Only steps 3 and 4 can promote a processor. Cross-builds and simulators are
screening evidence, never timing or power evidence.

## Local cross-compile

Run from the repository root:

```text
python tools/screen_audio_processor_candidates.py --compiler <arm-none-eabi-gcc>
```

The ignored `artifacts/local/audio-candidate-screen/` directory receives the
objects and `screen-result.json`. The current Arm profiles cover MIMXRT595,
STM32H563, and the portable Cortex-M55 path for Apollo510. ADSP-BF706/BF707 use
the Blackfin+ ISA and require the Analog Devices compiler; send the vendor pack
below to ADI rather than drawing conclusions from an Arm build.

## Vendor-operated run pack

Send the following repository files without modification:

- `../benchmark/`;
- `../common/`;
- `../../common/openref_audio_link.c` and `.h`;
- `vendor-run-request.md`; and
- `vendor-result-template.json`.

The recipient supplies only the LC3 callbacks, monotonic clock, 10 ms pacing,
serial/result export, and platform startup. Returned evidence must include the
ELF/map, raw log, result JSON, SDK/compiler identity, exact flags, and current
capture. Validate it with `tools/validate_audio_benchmark_result.py`.
