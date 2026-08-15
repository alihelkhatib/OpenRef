# Repository and Evidence Workflow

## What belongs where

| Location | Contents | Git policy |
|---|---|---|
| `docs/` | Requirements, architecture, standards, plans, and decisions | Commit |
| `simulator/` | Simulator source, scenarios, and tests | Commit source; ignore generated results |
| `firmware/` | Portable firmware source and board-specific integration notes | Commit source and reviewed notes |
| `hardware/` | Schematics, PCB source, and hardware decisions | Commit source; ignore fabrication exports |
| `mechanical/` | Enclosure and mechanical source | Commit source; ignore generated exports as added |
| `software/` | Future host/application software | Commit source |
| `tools/` | Reusable capture, runner, analyzer, and audit scripts | Commit |
| `artifacts/local/` | Raw local runs, logs, captures, binaries, and private bench details | Do not commit |

## Normal development loop

1. Start from a documented test plan or gate.
2. Create `artifacts/local/YYYY-MM-DD-short-description/` for exploratory or
   multi-board output. Existing Prototype 0 fixture runners may instead write
   ignored inputs to `firmware/prototype0/fg23/results/`.
3. Record the board roles, firmware hash, PHY/channel, RF path, test command,
   fixture setup, and pass criteria in the run README.
4. Keep raw serial logs and instrument exports unchanged.
5. Run the repository analyzer and retain its machine-readable summary beside
   the raw inputs.
6. If the run closes a gate, write a concise reviewed Markdown conclusion in
   the relevant firmware or testing directory and update the status rollup.
7. ZIP milestone evidence for durable external storage and record its SHA-256
   in the committed conclusion.

## Naming conventions

- Dates use ISO order: `YYYY-MM-DD` for directories and `YYYYMMDD` where an
  existing tool already emits that format.
- Use gate IDs when applicable: `e0-03-scheduled-tx-gpio`.
- Name roles, not temporary COM ports, in durable conclusions: `node-3-tx`.
- COM ports and board serial numbers may appear in ignored local raw data but
  should not become architectural project facts.

## Definition of evidence

A console message saying `PASS` is not sufficient by itself. Durable evidence
contains:

- the exact input or capture;
- the exact firmware or a reproducible firmware hash;
- the analyzer output and pass criteria;
- enough fixture context to reproduce the run;
- a concise reviewed conclusion linked from the relevant gate or status file.

Temporary pytest directories, cache folders, ad-hoc root output, and copied
console text are disposable workspace state—not project evidence.
