# P0 Support Fixture Design Review

Use this before ordering a support fixture PCB.

## Schematic Review

- [ ] All connectors are labeled with pin 1.
- [ ] Ground references are available near timing signals.
- [ ] Power entry and load direction are unambiguous.
- [ ] Current measurement path cannot accidentally bypass the meter.
- [ ] Audio loads are sized for expected power.
- [ ] Reset/fault injection cannot short supply rails.
- [ ] No final-product assumptions are hidden in fixture-only choices.

## Layout Review

- [ ] Test points are probeable.
- [ ] Silkscreen labels are readable.
- [ ] Mounting holes avoid traces and copper where required.
- [ ] High-current paths are wide enough for bench use.
- [ ] USB power paths are protected against accidental shorts where practical.
- [ ] Board outline leaves room for cables and clip leads.

## Fabrication Review

- [ ] Schematic PDF exported.
- [ ] Gerbers generated.
- [ ] Drill files generated.
- [ ] BOM exported.
- [ ] Assembly notes written.
- [ ] Revision marked on silkscreen.
- [ ] Known limitations documented.

## Bring-Up Review

- [ ] Continuity check plan written.
- [ ] Power-only smoke test defined.
- [ ] Current path verified with dummy load before dev board connection.
- [ ] Logic-analyzer header verified with static GPIO pattern.
- [ ] Audio loads verified with low-level signal before headset use.
