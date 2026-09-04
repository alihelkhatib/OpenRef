# OpenRef Audio Processor Benchmark

This directory is the vendor-neutral promotion test for an OpenRef audio
processor. It drives the production portable runtime with one encoder, five
independent decoder states, five-source mixing, deterministic PCM, and periodic
packet-loss concealment. A platform port supplies only codec and microsecond
clock callbacks.

## Fixed workload

- LC3, 10 ms frames, 16 kHz mono, signed 16-bit PCM;
- 40 encoded bytes per 10 ms frame (32 kbit/s);
- one encoder and five decoders on every block;
- five simultaneous remote sources through the production playout and mixer;
- deterministic packet loss on source six;
- 1,000 warmup blocks followed by 180,000 measured blocks (30 minutes);
- hard processing budget of 8,000 us per block.

Promotion output must also prove that exactly 181,000 target pacing ticks were
consumed with zero skipped ticks. Its elapsed timer interval must span the
1,810,000,000 us paced workload and no more than the final block's measured
processing time, with at most 1 ms additional interrupt-dispatch tolerance.
Synthetic or compute-only runs must use a different execution
mode and are deliberately rejected by the promotion validator.

The initial untimed encode produces a valid bitstream for remote decoder input.
The encode callback must copy the current frame into its output. For PLC,
decoder ports must invoke the codec's packet-loss path rather than decoding the
provided bytes as a valid frame.

## Port contract

1. Initialize one LC3 encoder and five independent LC3 decoders.
2. Provide a monotonic microsecond clock that continues running through codec
   and mixer execution. Timer wrap is acceptable when unsigned subtraction is
   correct over one block.
3. Populate `openref_audio_benchmark_hooks_t` and call
   `openref_audio_benchmark_init()`.
4. Call `openref_audio_benchmark_step()` from the 10 ms task until the result is
   complete. Do not run it in an interrupt handler.
5. Export every field in `openref_audio_benchmark_result_t`, plus the target
   identity, silicon revision, clock frequencies, timer source, memory
   placement, compiler, optimization flags, codec revision, firmware commit,
   stack high-water, measured current, and the current-measurement setup.

The step function deliberately does not delay. The target integration owns the
10 ms pacing so the benchmark includes its real scheduling environment. For an
isolated compute-only run, invoke each step as soon as the previous step
returns and label the result accordingly.

## Pass criteria

A promotion run passes only when:

- all 180,000 measured blocks complete;
- exactly 927 PLC calls occur during the measured interval (the deterministic
  missing second frame of source six every 97 packets, excluding warmup);
- encoder, decoder, and pipeline failure counts are zero;
- deadline misses are zero; and
- the maximum total processing time is at most 8,000 us.

Average timing alone never passes a target. A board is not promoted until the
same build also reports stack high-water and measured idle, one-talker, and
six-talker current. Desktop runs verify determinism and integration only; they
are not target-performance evidence.

## Machine-readable result

Emit one JSON object with this minimum shape:

```json
{
  "schema": "openref-audio-benchmark-v1",
  "benchmark_version": 1,
  "target": "vendor-part-and-board-revision",
  "execution_mode": "paced-target",
  "sample_rate_hz": 16000,
  "channel_count": 1,
  "sample_format": "signed-16-bit-pcm",
  "frame_duration_us": 10000,
  "codec_frame_bytes": 40,
  "encoder_count": 1,
  "decoder_count": 5,
  "plc_period_packets": 97,
  "warmup_blocks": 1000,
  "processing_budget_us": 8000,
  "clock_hz": 0,
  "silicon_revision": "revision",
  "compiler": "name-and-version",
  "optimization": "release flags",
  "codec": "implementation-and-revision",
  "firmware_commit": "git commit",
  "memory_placement": "code/data/codec placement",
  "clock_configuration": "core, bus, accelerator, and memory clocks",
  "timer_source": "timer peripheral, width, frequency, and clock source",
  "current_measurement": "measurement point, instrument, sample rate, and board operating conditions",
  "requested_blocks": 180000,
  "completed_blocks": 0,
  "plc_calls": 0,
  "encode_failures": 0,
  "decode_failures": 0,
  "process_failures": 0,
  "deadline_misses": 0,
  "maximum_encode_us": 0,
  "maximum_render_us": 0,
  "maximum_total_us": 0,
  "average_encode_us": 0,
  "average_render_us": 0,
  "average_total_us": 0,
  "stack_high_water_bytes": 0,
  "idle_current_ma": null,
  "one_talker_current_ma": null,
  "six_talker_current_ma": null,
  "complete": false,
  "passed": false
}
```

Use `null`, not zero, for measurements that were not performed. Store raw logs,
the ELF/map files, and the JSON result together so reported firmware can be
reproduced. `timer_source` must identify enough of the monotonic-clock
implementation to assess resolution and wrap behavior. `current_measurement`
must identify the electrical measurement point, instrument, sample rate, and
conditions shared by the three current measurements (for example supply
voltage and whether radios or debug probes were enabled).

Before accepting a promotion result, run:

```text
python tools/validate_audio_benchmark_result.py result.json
```

The validator intentionally rejects `null` current measurements: incomplete
results may retain them while measurements are pending, but they are not
promotion evidence.
