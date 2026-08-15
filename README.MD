# OpenRef

OpenRef is an open-source professional communication system for sports match officials.
The goal is reliable, accessible, professional-grade crew audio for rugby and
soccer officials without phones, internet service, cloud services, or venue
infrastructure.

## Current Phase

OpenRef is in requirements refinement and Prototype 0 preparation.

Prototype 0 focuses on network feasibility:

- six simultaneous voice nodes;
- scheduled shared-medium transport;
- packet loss, latency, and queue behavior;
- coordinator heartbeat, failure, and election behavior;
- early evidence for radio, topology, codec, latency, and power decisions.

See [docs/program/program-status.md](docs/program/program-status.md) and
[docs/program/prototype-roadmap.md](docs/program/prototype-roadmap.md).

## Repository Map

| Path | Purpose |
|---|---|
| `docs/` | Product, requirements, architecture, standards, testing, compliance, and program docs. |
| `simulator/` | Deterministic Python simulator for early radio scheduling and recovery analysis. |
| `firmware/` | Firmware workspace placeholder for Prototype 0 and later embedded work. |
| `hardware/` | Electronics workspace placeholder. |
| `mechanical/` | Mechanical and enclosure workspace placeholder. |
| `software/` | Desktop/mobile/service software workspace placeholder. |
| `tools/` | Engineering scripts and local tooling workspace placeholder. |
| `artifacts/` | Local run-data convention and external archival guidance. |

See [Repository and Evidence Workflow](docs/program/repository-workflow.md) for
where generated bench output belongs and how milestone evidence is archived.

## Simulator Quick Start

```bash
cd simulator
python -m pip install -e ".[dev]"
python -m pytest
python -m openref_sim.cli scenarios/six_nodes_nominal.yaml \
  --trace results/nominal-trace.csv \
  --summary results/nominal-summary.json
python -m openref_sim.sweep scenarios/six_nodes_nominal.yaml \
  --csv results/prototype-0-sweep.csv
```

## Near-Term Build Direction

1. Use the simulator to compare candidate Prototype 0 schedules, codec bitrates,
   packetization intervals, and radio bitrates.
2. Convert the strongest scenarios into architecture verification evidence.
3. Select development-board radio candidates for measured six-node tests.
4. Replace simulator assumptions with measured airtime, current draw, latency,
   and recovery data.
