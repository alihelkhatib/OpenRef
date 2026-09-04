# ADSP-BF706 LC3 qualification result

Date: 2026-08-31

## Decision

The ADSP-BF706 is not qualified as a production target for the canonical
OpenRef audio workload. It runs the codec correctly and completes many frames
inside 10 ms, but measured deterministic and live inputs exceed the hard
deadline. It remains useful as a development and functional-validation target.

## Workload and platform

- ADSP-BF706 EZ-KIT Mini, silicon revision 1.1
- CCES 2.12.1 and `ccblkfn`
- Measured 400 MHz core clock
- 16 kHz mono signed-16 PCM, 10 ms/160-sample frames
- 40-byte LC3 frames (32 kb/s)
- one encoder, five independent persistent decoders, and five-stream mixing
- hard deadline: less than 4,000,000 cycles (10 ms)
- preferred processor-selection gate: no more than 3,200,000 cycles (8 ms)

## Principal measurements

| Test | Result | Interpretation |
|---|---:|---|
| Reproduced portable baseline | 5,811,033 cycles (14.528 ms) | Fail |
| Q31/SIMD optimized milestone | 3,542,451 cycles (8.856 ms) | Meets 10 ms on this input only |
| Deterministic mixed corpus, 30,000 frames | 4,028,539 cycles (10.071 ms), 23 misses | Reproducible hard-deadline failure |
| Same corpus without profiling | 4,027,087 cycles, 22 misses | Failure is not profiling overhead |
| Targeted slow frame with vectorized store | 4,025,909 cycles | Optimization remains insufficient |
| Final live SPORT/ADAU1761, 10,000 frames | 5,015,415 cycles (12.539 ms), 502 misses | Independent live failure |

The deterministic slow input is frame 21,605 in the low-level-noise class. Its
approximate decomposition is 1,449,149 encoder cycles, about 514,000 cycles for
each of five decoders, and 8,338 mixing cycles. Mixing is negligible; codec
execution, particularly the five decoders collectively, dominates.

## Successful validation

- Encoder and all five decoder instances initialized and returned expected
  status values throughout the reported normal, PLC, corruption, and live runs.
- Two 10,000-frame stateful pseudorandom runs had zero misses and zero codec
  errors; their maximum was 2,171,140 cycles.
- A 10,000-frame run with one lost packet every tenth frame performed 5,000 PLC
  operations with zero unexpected returns and a 2,172,222-cycle maximum.
- A 10,000-frame run corrupting every tenth packet recovered with zero
  unexpected returns and a 2,951,619-cycle maximum.
- Direct placement of three decoder states in L1-A and two in L1-B produced
  clean 10,000- and 30,000-frame live runs with a 3,224,162-cycle maximum, but
  later tests proved that this was not the all-input worst case.
- Physical-board SQAM testing covered nine decoder and encoder items. All
  decoder 14-bit criteria and all encoder delta-ODG criteria passed, with zero
  codec errors. This is interoperability evidence, not a Bluetooth SIG listing.

## Fixed-point/SIMD gate

The Apache-licensed BF706 Q31 mixed-radix 80-point FFT reduced an otherwise
comparable complete benchmark from 4,530,188 to 3,542,451 cycles, a 21.80%
improvement. Tested encoded packets were bit-exact; decoded PCM was bit-exact
or differed by at most one signed-16 count.

That optimization was already present in the 4,025,909-cycle replayable slow
frame. Reaching the 3.2-million-cycle selection gate would therefore require a
further measured saving of 825,909 cycles. No bounded follow-on experiment
demonstrated a credible saving of that scale. A local fixed-point LC3plus tree
was not imported because its stated ETSI licensing is not suitable for direct
inclusion in permissively licensed OpenRef code.

## Meaning for processor selection

The codec is functionally sound, and the board is fast enough for demos and
many ordinary frames. It is not fast enough to reserve dependable time for
radio work, encryption, synchronization, interrupts, controls, and future
audio processing while guaranteeing every 10 ms deadline. Future MCU
comparisons must use execution time and utilization, preserve the exact slow
frame, and require physical-target measurements before declaring a pass.

The permanent regression vector is
`firmware/audio_processor/benchmark/vectors/bf706-worstcase-21605.json`.
Raw captures and toolchain-specific projects remain local engineering
artifacts because they include large binaries and machine-specific files.
