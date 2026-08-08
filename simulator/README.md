# OpenRef Simulator v0.2

Deterministic discrete-event simulation of OpenRef voice traffic, radio airtime,
collisions, packet-loss bursts, node clock drift, bounded queues, audio
deadlines, coordinator heartbeat, failure, and election.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

## Run scenarios

```bash
openref-sim scenarios/six_nodes_drift.yaml \
  --trace results/drift-trace.csv \
  --summary results/drift-summary.json

openref-sim scenarios/coordinator_failure.yaml \
  --trace results/coordinator-failure-trace.csv \
  --summary results/coordinator-failure-summary.json

openref-sim scenarios/packet_loss_burst.yaml \
  --trace results/packet-loss-burst-trace.csv \
  --summary results/packet-loss-burst-summary.json
```

Generated `results/*.csv` and `results/*.json` files are ignored by Git.

## Sweep Architecture Parameters

Use `openref-sweep` to compare codec bitrate, packetization interval, radio
bitrate, and slot spacing against the Prototype 0 screening criteria.

```bash
openref-sweep scenarios/six_nodes_nominal.yaml \
  --frame-ms 10,20 \
  --codec-bps 16000,24000,32000 \
  --radio-bps 250000,500000,1000000 \
  --slot-us 1000,1500,2000,2500,3000 \
  --csv results/prototype-0-sweep.csv \
  --markdown results/prototype-0-sweep.md
```

The sweep sorts feasible cases first. A case is screened as feasible when it has
no simulated voice collisions, no queue overflows, no audio deadline misses,
enough delivery ratio, a schedule that fits within the audio frame, and planned
channel utilization at or below the configured maximum.

## Scenario Inputs

Scenario YAML files define:

- `duration_seconds`: simulation duration;
- `nodes`: a node count or explicit node IDs with `drift_ppm`;
- `audio`: frame duration, encoded bitrate, optional queue depth, and deadline;
- `radio`: bitrate, packet overhead, preamble, propagation delay, and optional
  base loss probability;
- `schedule`: per-node slot spacing;
- `protocol`: coordinator heartbeat, timeout, election delay, and initial
  coordinator;
- `faults`: optional `disable_node`, `enable_node`, or `packet_loss` events.

Invalid fault actions and unknown node IDs fail loudly so scenario mistakes do
not produce misleading evidence.

## Interpretation

The model is an architecture simulator, not an RF propagation certification
tool. Its assumptions must be replaced with measurements from candidate
development boards as those measurements become available.
