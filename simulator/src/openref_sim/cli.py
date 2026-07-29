from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import write_trace_csv
from .run import run_scenario
from .scenario import load_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an OpenRef simulation scenario")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--trace", type=Path, default=Path("results/trace.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/summary.json"))
    args = parser.parse_args()

    scenario = load_scenario(args.scenario)
    simulation, summary = run_scenario(scenario)
    write_trace_csv(simulation.trace, args.trace)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Scenario: {scenario.name}")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"Trace: {args.trace}")
    print(f"Summary: {args.summary}")


if __name__ == "__main__":
    main()
