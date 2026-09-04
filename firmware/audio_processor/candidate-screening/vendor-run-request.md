# OpenRef Vendor-Operated Audio Benchmark Request

Please run the enclosed unmodified OpenRef audio benchmark on the proposed
production processor. The fixed workload is 16 kHz mono LC3 at 32 kbit/s: one
encode, five independent decodes, five-source mixing, and deterministic PLC in
every 10 ms interval.

Please provide:

- processor, silicon revision, board and board revision;
- SDK, LC3 implementation/revision, compiler/version, and exact release flags;
- core, DSP/accelerator, bus and memory clocks plus code/data placement;
- a paced 30-minute result containing all JSON fields in the template;
- stack high-water and idle, one-talker, and six-talker current;
- electrical measurement point, voltage, instrument, sample rate, and debug/radio state;
- raw console log, ELF, linker map, and a source/archive hash.

The pass threshold is zero failures and deadline misses, with worst-case total
processing time no greater than 8,000 us. Please do not replace worst-case
timing with an average or run the steps back-to-back; the benchmark must consume
one real 10 ms pacing tick per block.
