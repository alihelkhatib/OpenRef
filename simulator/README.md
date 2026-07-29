# OpenRef Simulator v0.1

A deterministic discrete-event simulator for testing whether six continuous OpenRef voice streams fit into a fixed-slot sub-GHz radio schedule.

## What v0.1 models

- six configurable nodes;
- encoded voice frames represented as packet payloads;
- radio airtime from bitrate, payload, overhead, and preamble;
- fixed transmission slots;
- a shared single-channel medium;
- collisions when transmissions overlap;
- delivery latency;
- CSV event traces and JSON summaries.

It does not yet model elections, clock drift, retransmission, RF fading, actual codecs, or audio mixing.

## Setup

```bash
cd simulator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

## Run the nominal scenario

```bash
openref-sim scenarios/six_nodes_nominal.yaml \
  --trace results/nominal-trace.csv \
  --summary results/nominal-summary.json
```

## Run the deliberately failing collision scenario

```bash
openref-sim scenarios/six_nodes_collision.yaml \
  --trace results/collision-trace.csv \
  --summary results/collision-summary.json
```

## Baseline calculation

With the supplied nominal scenario:

- 20 ms audio frames;
- 24 kbps encoded voice;
- 60-byte payload;
- 16-byte packet overhead;
- 500 kbps radio bitrate;
- 100 microseconds preamble allowance.

Each packet occupies 1,316 microseconds. Six packets occupy 7,896 microseconds of every 20,000-microsecond frame period before guard time and control traffic. The fixed 2,500-microsecond slot spacing therefore has substantial initial margin.

## Next release

v0.2 should add:

1. node-local clocks and drift;
2. coordinator heartbeat and election;
3. packet-loss and interference bursts;
4. transmit queues and deadline misses;
5. parameter sweeps across codec and radio bitrates.
