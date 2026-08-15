# Prototype 1 Wearable Electronics

Prototype 1 is the first custom electronics architecture after Prototype 0
network feasibility evidence.

The current baseline integrates an FGM230SB FG23 radio/network SiP, a separate
audio processor, headset codec/front end, controls, diagnostics, and a removable
protected 1-cell battery. Architecture inputs are:

- `docs/interfaces/ICD-005-radio-audio-processor.md`;
- `docs/power/prototype1-power-tree.md`;
- `docs/adr/ADR-0006-prototype-audio-processor-platform.md`;
- `hardware/prototype1-wearable/pre-schematic-architecture.md`;
- `hardware/prototype1-wearable/electrical-interface-contract.json`;
- `hardware/prototype1-wearable/fgm230sb-pin-allocation.json`;
- `hardware/prototype1-wearable/schematic-connectivity.json`;
- `hardware/prototype1-wearable/wearable-mechanical-contract.json`;
- `docs/mechanical/wearable-integration-baseline.md`;
- `hardware/prototype1-wearable/cad/fgm230sb-footprint-requirements.md`;
- `hardware/prototype1-wearable/cad/openref-fgm230sb.kicad_sym`;
- `hardware/prototype1-wearable/cad/OpenRef-FGM230SB.pretty/FGM230SB27HGN3.kicad_mod`;
- `tools/generate_fgm230_kicad_library.py`;
- `tools/validate_fgm230_kicad_library.py`;
- `tools/validate_fgm230_sdk_routes.py`;
- `tools/validate_prototype1_connectivity.py`;
- `tools/validate_wearable_mechanical_contract.py`;
- `firmware/prototype0/fg23/20260814-openref-80-byte-network-result.md`.

Do not begin custom wearable schematic capture until the readiness checklist is
satisfied or explicitly waived.

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

- production radio cost optimization beyond the Prototype 1 SiP baseline;
- antenna architecture;
- audio codec part number and analog component values;
- regulator, protection, and supervisor part numbers;
- connector family;
- enclosure-driven board outline.

The analog-headset direction, removable protected 1S pack, external charging,
separate audio processor, processor-link contract, power-domain structure, and
debug/test philosophy are already architectural baselines. They should not be
reported as wholly undecided merely because component values remain gated.

The native FGM230SB library is reproducibly tied to the controlled 48-pin CSV
and the manufacturer's revision 1.2 Figure 8.4 dimensions. Run
`python tools/validate_fgm230_kicad_library.py` after any CAD-library change.
This independent check does not replace native KiCad parsing or schematic ERC.
