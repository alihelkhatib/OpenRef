# Prototype 0 Simulator Screening

**Document ID:** OR-TST-005
**Revision:** 0.1
**Status:** Initial simulator-only screening

## Purpose

Use the deterministic simulator to narrow Prototype 0 network candidates before
development-board measurements begin.

This document is not RF evidence. It records analytical screening results and
the command needed to regenerate them.

## Current Sweep Command

From `simulator/`:

```bash
python -m openref_sim.sweep scenarios/six_nodes_nominal.yaml \
  --frame-ms 10,20 \
  --codec-bps 16000,24000,32000 \
  --radio-bps 250000,500000,1000000 \
  --slot-us 1000,1500,2000,2500,3000 \
  --csv results/prototype-0-sweep.csv \
  --markdown results/prototype-0-sweep.md
```

If the package is not installed in editable mode, run with `PYTHONPATH=src`.

## Screening Criteria

A swept case is marked feasible when:

- delivery ratio is at least 99.9%;
- simulated voice collisions are zero;
- queue overflows are zero;
- audio deadline misses are zero;
- planned channel utilization is at or below 75%;
- the six-node schedule fits inside the audio frame interval.

## Current Nominal Result

The initial sweep covers 90 combinations.

| Radio bitrate | Feasible cases | Infeasible cases |
|---:|---:|---:|
| 1,000,000 bps | 18 | 12 |
| 500,000 bps | 13 | 17 |
| 250,000 bps | 2 | 28 |

The current nominal baseline, 20 ms frames, 24 kbps encoded voice, 500 kbps
radio bitrate, and 2500 us slot spacing, remains feasible in the simulator:

- planned channel utilization: 39.964%;
- voice packet airtime: 1316 us;
- heartbeat packet airtime: 484 us;
- per-slot guard: 1184 us;
- six-node schedule span: 13,816 us inside a 20,000 us frame;
- simulated delivery ratio: 100%;
- simulated voice collisions: 0.

## Interpretation

The first simulator result supports continuing to evaluate 500 kbps-class radios
for Prototype 0. It does not down-select the radio band or silicon.

The next evidence must come from boards:

- measured scheduled transmit launch error;
- measured useful payload throughput;
- measured current in coordinator and member roles;
- measured packet loss and latency under attenuation;
- measured coexistence behavior near Wi-Fi and Bluetooth traffic.
