# OpenRef Simulator v0.2

Deterministic discrete-event simulation of OpenRef voice traffic, radio airtime, collisions, packet-loss bursts, node clock drift, bounded queues, audio deadlines, coordinator heartbeat, failure, and election.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
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

## Interpretation

The model is an architecture simulator, not an RF propagation certification tool. Its assumptions must be replaced with measurements from the FG23 development kits as those measurements become available.
