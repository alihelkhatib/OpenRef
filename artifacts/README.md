# Engineering Artifacts

This directory is the landing area for generated test and bench output that
does not belong at the repository root.

## Local runs

Store each run under:

```text
artifacts/local/YYYY-MM-DD-short-description/
```

Suggested contents:

```text
README.md       Human context: hardware, firmware, setup, result, anomalies
raw/            Serial logs and instrument exports
summary/        Analyzer JSON, CSV summaries, plots, and tables
firmware/       Exact HEX/ELF used for the run, when needed for reproduction
photos/         Local setup photos with private labels/serials removed
```

`artifacts/local/` is ignored by Git because runs can contain large files,
machine-specific COM ports, board serial numbers, and transient failures.

## Evidence committed to Git

Commit a concise Markdown conclusion only after reviewing the local run. Put
Prototype 0 FG23 conclusions under `firmware/prototype0/fg23/` and link them
from the relevant gate/status document. Generated inputs used by the existing
gate tooling remain under `firmware/prototype0/fg23/results/`; that path is
ignored except for its README.

## External archive

For a gate-closing or milestone run, preserve the complete local run directory
in durable external storage. Archive it as a ZIP named:

```text
openref-YYYY-MM-DD-gate-or-test-short-description.zip
```

Record the ZIP SHA-256 in the committed Markdown conclusion. The archive
should include the run README, raw inputs, analyzer outputs, exact firmware,
and any fixture configuration needed to reproduce the result.
