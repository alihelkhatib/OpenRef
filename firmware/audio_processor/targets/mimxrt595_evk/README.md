# MIMXRT595-EVK Audio Validation Target

This directory is the target boundary for the first complete OpenRef audio
bench. The portable pipeline and runtime are ready; MCUXpresso-generated clock,
pin, DMA, DMIC, WM8904, and Flexcomm files belong here after the board and SDK
are available.

## Starting SDK example

Begin from NXP's `dmic_i2s_codec` example for EVK-MIMXRT595. It already proves
the onboard DMIC-to-WM8904 path. Preserve its clock and codec initialization,
replace its PCM copy loop with 160-sample ping-pong DMA blocks, and invoke
`openref_audio_runtime_process()` once for every completed 10 ms capture block.
Use 16 kHz, signed 16-bit, mono processing internally; duplicate the limited
mono result into both codec channels only at the playback boundary.

The official audio demo requires headphones on J4 and documents jumpers JP7,
JP8, JP27, JP28, and JP29 in positions 1-2. Confirm the actual board revision
and jumper labels before applying power.

## Processor-link bench wiring

The FG23 remains the SPI controller. The RT595 target is a full-duplex SPI
peripheral with one active-low request output. Use an exposed RT595 Flexcomm or
PMOD SPI instance and keep all signals at 3.3 V logic.

For BRD2600A, the provisional non-debug pin allocation is:

| Link signal | FG23 breakout | FG23 role |
|---|---|---|
| COPI | PA7, pad 12 | SPI controller output |
| CIPO | PA8, pad 13 | SPI controller input |
| SCLK | PB0, pad 14 | SPI controller clock |
| CSn | PB1, pad 10 | SPI controller select |
| AUDIO_REQn | PB2, pad 11 | GPIO input |
| AUDIO_RESETn | PB3, pad 15 | GPIO output |
| Ground | GND, pad 17 | Common reference |

Disable the BRD2600A Si7021, LC sensor, button 0, and LED before assigning these
pins. Do not use PA1 or PA2 for this link: they are SWCLK and SWDIO, and must
remain available for programming and debug. The existing PA1/PA2/PB2/PB3 scope
wires are test instrumentation, not all four SPI wires.

During initial bring-up, power both boards independently from USB and connect
only the common ground and logic signals. Do not join 5 V, 3.3 V, or VMCU rails.
Add 22-47 ohm source-series resistance on SCLK and COPI if edge ringing is
visible; the production schematic retains configurable series footprints.

## Bring-up sequence

1. Run the unmodified NXP DMIC-to-headphone example and verify clean local
   loopback at conservative headphone volume.
2. Convert the example to 160-sample ping-pong DMA and verify exactly 100 block
   completions per second with no overrun.
3. Integrate the portable runtime with a deterministic codec stub; require zero
   deadline misses for 30 minutes.
4. Integrate one LC3 encoder and five decoder states. Log maximum encode,
   render, and total times; total must remain at or below 8 ms.
5. Add 8 MHz SPI and exchange the fixed 98-byte frame. Inject CRC corruption,
   sequence gaps, processor reset, and queue overflow.
6. Run microphone-to-radio and radio-to-headphone simultaneously for one hour,
   then repeat with five remote sources and forced packet loss.
7. Measure idle, local loopback, one-talker, and six-talker current before
   promoting the processor choice.

## Promotion evidence

Store serial logs, firmware hashes, SDK version, board revision, jumper state,
timing maxima, stack high-water, and current captures under an ignored dated
artifact directory. Summarize the reproducible result in a tracked Markdown
report; do not promote the platform from an audible-only demonstration.
Start from `benchmark-result-template.json` and run the repository benchmark
validator with `--require-promotion` before accepting this processor.

The v2 result must identify real 16 kHz, 160-sample ping-pong DMA operation,
one encoder and five decoder instances, zero capture overrun, playback
underrun, and pacing misses, at least 20% reserved-stack and total-memory
margin, and measured idle/one-talker/six-talker current. Record SHA-256 hashes
for the serial log, ELF, and linker map; a compute-only loop cannot be promoted.

Keep the populated result and all three artifacts in one dated directory, then
bind their actual bytes into the result without manually copying hashes:

```text
python tools/package_audio_benchmark_evidence.py raw-result.json \
  --serial-log evidence/serial.log \
  --elf evidence/openref_audio_benchmark.elf \
  --map evidence/openref_audio_benchmark.map \
  --output evidence/result.json
```

Promotion validation must resolve and re-hash the recorded files:

```text
python tools/validate_audio_benchmark_result.py evidence/result.json \
  --require-promotion --artifact-root evidence
```

The packager refuses empty files, artifacts outside the output directory, and
replacement of an existing result unless `--force` is explicit.

Official references:

- <https://www.nxp.com/design/design-center/development-boards-and-designs/i-mx-evaluation-and-development-boards/i-mx-rt595-evaluation-kit%3AMIMXRT595-EVK>
- <https://mcuxpresso.nxp.com/mcuxsdk/latest/html/examples/driver_examples/dmic/dmic_i2s_codec/readme.html>
- <https://www.silabs.com/documents/public/user-guides/ug508-brd2600a-user-guide.pdf>
