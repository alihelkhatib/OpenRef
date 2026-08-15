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
   identity, silicon revision, clock frequencies, memory placement, compiler,
   optimization flags, codec revision, firmware commit, stack high-water, and
   measured current.

The step function deliberately does not delay. The target integration owns the
10 ms pacing so the benchmark includes its real scheduling environment. For an
isolated compute-only run, invoke each step as soon as the previous step
returns and label the result accordingly.

## Pass criteria

A promotion run passes only when:

- all 180,000 measured blocks complete;
- PLC is exercised;
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
  "schema": "openref-audio-benchmark-v2",
  "target": "vendor-part-and-board-revision",
  "board_revision": "board revision",
  "silicon_revision": "silicon revision",
  "sdk_version": "SDK version",
  "execution_mode": "paced-target",
  "audio_io_mode": "ping-pong-dma",
  "clock_hz": 0,
  "sample_rate_hz": 16000,
  "block_samples": 160,
  "encoder_instances": 1,
  "decoder_instances": 5,
  "compiler": "name-and-version",
  "optimization": "release flags",
  "codec": "implementation-and-revision",
  "firmware_commit": "git commit",
  "requested_blocks": 180000,
  "completed_blocks": 0,
  "plc_calls": 0,
  "encode_failures": 0,
  "decode_failures": 0,
  "process_failures": 0,
  "deadline_misses": 0,
  "capture_dma_overruns": 0,
  "playback_dma_underruns": 0,
  "pacing_deadline_misses": 0,
  "maximum_encode_us": 0,
  "maximum_render_us": 0,
  "maximum_total_us": 0,
  "average_encode_us": 0,
  "average_render_us": 0,
  "average_total_us": 0,
  "stack_high_water_bytes": 0,
  "stack_reserved_bytes": 0,
  "static_memory_bytes": 0,
  "memory_capacity_bytes": 0,
  "idle_current_ma": null,
  "one_talker_current_ma": null,
  "six_talker_current_ma": null,
  "complete": false,
  "passed": false,
  "artifact_sha256": {
    "serial_log": "64 hexadecimal characters",
    "elf": "64 hexadecimal characters",
    "map": "64 hexadecimal characters"
  }
}
```

Use `null`, not zero, for measurements that were not performed. Store raw logs,
the ELF/map files, and the JSON result together so reported firmware can be
reproduced.

Validate a captured result with
`python tools/validate_audio_benchmark_result.py RESULT.json`. Add
`--require-promotion --artifact-root ARTIFACT_DIRECTORY` when using the result
to select the processor; strict mode
requires real ping-pong DMA audio I/O, correct block geometry, zero DMA/pacing
faults, clock evidence, at least 20% stack and static-memory margin, all three
current measurements, and SHA-256 identities for the serial log, ELF, and map.
The target template is
`firmware/audio_processor/targets/mimxrt595_evk/benchmark-result-template.json`.
Use `tools/package_audio_benchmark_evidence.py` to populate the controlled
relative artifact filenames and hashes from the actual captured files.
