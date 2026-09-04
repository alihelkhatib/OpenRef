# Prototype 1 Wearable Electronics

Prototype 1 is the first custom electronics architecture after Prototype 0
network feasibility evidence.

The current baseline integrates the FG23 radio/network processor, a separate
audio processor, headset codec/front end, controls, diagnostics, and a removable
protected 1-cell battery. Architecture inputs are:

- `docs/interfaces/ICD-005-radio-audio-processor.md`;
- `docs/power/prototype1-power-tree.md`;
- `docs/adr/ADR-0006-prototype-audio-processor-platform.md`;
- `hardware/prototype1-wearable/pre-schematic-architecture.md`;
- `firmware/prototype0/fg23/20260814-openref-80-byte-network-result.md`.

Do not begin custom wearable schematic capture until the readiness checklist is
satisfied or explicitly waived.

The nine currently open inputs have a machine-checkable intake template at
`readiness-inputs-template.json`. Create a dated copy, replace an item's
`open` status only after recording its concrete value or decision, reviewer,
timezone-qualified timestamp, and SHA-256-bound evidence, then run:

```text
python tools/prototype1_readiness_inputs.py --check --json path/to/readiness-inputs.json
```

The checker exits nonzero while any input remains open. Passing validation is
evidence intake, not permission to check a readiness item whose recorded result
fails its engineering acceptance criterion.

## Expected Scope

- processor or wireless SoC/module;
- radio front end or certified module;
- audio input and output path;
- power regulation;
- battery interface;
- controls and status indicators;
- debug/programming connector;
- production-test access.

## Deferred Until Required Evidence

- final radio silicon/module;
- antenna architecture;
- audio codec part number and analog component values;
- regulator, protection, and supervisor part numbers;
- connector family;
- enclosure-driven board outline.

The analog-headset direction, removable protected 1S pack, external charging,
separate audio processor, processor-link contract, power-domain structure, and
debug/test philosophy are already architectural baselines. They should not be
reported as wholly undecided merely because component values remain gated.

The Prototype 1 wireless partition is likewise closed at the architecture
level: a separate FG23 radio/network processor on the sub-GHz path. This does
not promote the development-board device or commit the production design to a
part package, module, RF match, or antenna. Those choices remain gated by
secured-packet airtime, current profiles, supply/lifecycle review, and
enclosure/body-loss evidence.
