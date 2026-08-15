# Audio Processor Resource Budget

**Document ID:** OR-ARC-015
**Revision:** 0.1
**Status:** Static footprint measured; target timing and stack pending

## ARM ABI Static State

The portable structures were compiled for Cortex-M33 with the Silicon Labs GCC
14.2.1 toolchain and measured from ELF symbols:

| Object | Bytes |
|---|---:|
| Processor-link frame | 96 |
| Four-entry processor-link queue | 400 |
| Capture packetizer including output queue | 504 |
| One encoded playout source | 452 |
| Six-source playout state | 2,712 |
| Mixer state | 32 |
| Complete portable pipeline state | 3,260 |
| Complete target-facing runtime state | 3,308 |

The fixed 98-byte wire representation is deliberately not the same as the
96-byte aligned in-memory frame structure.

## Codec and Buffer Baseline

| Allocation | Bytes |
|---|---:|
| One LC3 encoder state | 2,600 |
| Five LC3 decoder states | 15,720 |
| Portable runtime state | 3,308 |
| Double-buffered 16 kHz capture PCM | 640 |
| Double-buffered 16 kHz playback PCM | 640 |
| **Known persistent subtotal** | **22,908** |

This subtotal excludes SDK/RTOS state, peripheral drivers, stack, diagnostic
capture, security, update, and alignment overhead. The codec benchmark added
about 81 KB text and 628 bytes initialized data to the FG23 development image;
the final audio target must be measured independently.

## Initial Processor Floor

Before target measurements justify a reduction, an audio-processor candidate
shall provide at least:

- 128 KB SRAM and 512 KB nonvolatile program storage;
- hardware floating point or a demonstrated fixed-point LC3 path;
- DMA-capable microphone input, audio output, and SPI;
- independent watchdog and deterministic 10 ms scheduling;
- enough throughput for encode, five decodes, mixing, and I/O in no more than
  8 ms per interval.

RT595 exceeds the memory floor substantially. Its selection remains contingent
on measured execution, stack high-water, active power, and toolchain viability.

## Measurements Still Required

- release-optimized LC3 and mixer execution on RT595 M33 and, if needed, DSP;
- main/audio-task stack high-water under packet loss and five active sources;
- DMA buffer placement and cache-coherency overhead;
- code size with production diagnostics and update support;
- worst-case processor-link interrupt latency;
- current at idle, one talker, and six continuous talkers.
