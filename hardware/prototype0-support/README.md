# Prototype 0 Support Hardware

This track contains bench fixtures that support FG23 dev-board testing.

The first useful PCB is a support fixture, not a custom wearable radio board.

## Candidate Board

`p0-support-fixture`

Purpose:

- make E0-02 packet-pair and E0-03 scheduled-TX measurements repeatable;
- expose clean logic-analyzer points;
- simplify current measurement;
- provide safe audio loads and loopback connection points;
- provide reset/fault-injection access.

## Design Constraints

- no RF matching network decisions;
- no final battery decisions;
- no final headset connector decision;
- no product miniaturization;
- easy probing and labeling matter more than size.

## Suggested Tooling

Use KiCad unless a different EDA tool is explicitly selected.

Commit source files only after the project template, libraries, and generated
outputs are understood. Generated fabrication outputs should live under ignored
`generated/` directories.
