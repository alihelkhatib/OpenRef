# FGM230SB CAD Intake Requirements

**Document ID:** OR-HW-007  
**Revision:** 0.2  
**Status:** Native library generated and dimensionally checked; KiCad parse/reviewer approval pending

## Authoritative inputs

- Ordering code: `FGM230SB27HGN3`.
- Manufacturer data sheet: FGM230S Proprietary SiP Module Data Sheet,
  revision 1.2, November 2024.
- Package: 48-pad, 6.500 mm square SiP, nominal height 1.180 mm.
- Manufacturer land-pattern table: data-sheet section 8.2. Do not infer pad
  locations from a rendered symbol or from the BRD2600A development board.
- Controlled logical source: `../fgm230sb-pin-allocation.json`.
- Reproducible symbol import table: `fgm230sb-symbol-pins.csv`.
- Native symbol: `openref-fgm230sb.kicad_sym`.
- Native footprint: `OpenRef-FGM230SB.pretty/FGM230SB27HGN3.kicad_mod`.
- Generator and check: `../../../tools/generate_fgm230_kicad_library.py` and
  `../../../tools/validate_fgm230_kicad_library.py`.

Official source:
<https://www.silabs.com/documents/public/data-sheets/fgm230s-datasheet.pdf>

## Footprint constraints

The native EDA footprint shall reproduce the complete manufacturer section 8.2
land pattern and courtyard. Table values include `D1 = 5.00 mm`, `D2 = 2.90
mm`, `E1 = 5.00 mm`, `E2 = 2.90 mm`, `eD1 = 0.45 mm`, `eD2 = 0.90 mm`, `eE1
= 0.45 mm`, `eE2 = 0.90 mm`, `b = 0.25 mm`, `e = 0.50 mm`, `L = 0.35 mm`,
and `L1 = 0.50 mm`. These values are acceptance references, not enough by
themselves to reconstruct ambiguous pad coordinates without Figure 8.4.

Figure 8.4 was visually inspected from the controlled revision 1.2 PDF. It
establishes 0.50 mm perimeter pitch; top/bottom row centers from -2.50 mm to
+2.50 mm at y = +/-2.90 mm; side-row centers from -2.50 mm to +2.50 mm at
x = +/-2.90 mm; and central-pad centers at (+/-0.45 mm, +/-0.45 mm). Pads
1-44 use 0.25 x 0.35 mm lands oriented radially and pads 45-48 use 0.50 mm
square lands.

Use a 0.100 mm stencil and 80% paste coverage as the initial manufacturer
recommendation. Separate centered paste apertures provide 80% copper-pad area
without relying on EDA-specific paste-margin interpretation. The assembly house
must review paste segmentation, stencil,
reflow, X-ray/inspection access, and escape routing. Record any change rather
than silently editing the library.

## Symbol constraints

- All 48 pins appear exactly once and retain manufacturer pin numbers.
- Pins 18 `DECOUPLE` and 24 `VDCDC` are explicit no-connect pins.
- Pins 2, 4, 27, and 44-48 are ground and remain individually visible for
  connectivity checking.
- Pins 25 `VREGVDD` and 26 `IOVDD` remain separate symbol pins even though both
  connect to `V_RADIO`.
- Pin 3 `RFIO` is an RF/passive pin, not a generic digital output.
- PA1/PA2/PA3 remain SWCLK/SWDIO/SWO and must not be hidden power pins or
  alternate controls.

## Sheet 03 implementation checklist

- Place one local minimum 10 uF capacitor at each VREGVDD and IOVDD pin, plus
  smaller/bulk footprints only when supported by the final impedance review.
- Expose SWCLK, SWDIO, SWO, RESETn, V_RADIO reference, and GND to the fixture.
- Expose UART TX/RX and PTI FRAME/DATA without routing them through user-accessible
  conductors in the enclosure.
- Pull `AUD_RESET_N` low in hardware and isolate the V_RADIO/V_AUDIO crossing.
- Pull active-low asynchronous inputs to their inactive state in the receiving
  domain; internal pulls are not the only safety mechanism across powered-off
  domains.
- Provide the removable V_RADIO current link and rail test point required by
  OR-HW-005.

## Sheet 08 implementation checklist

- Route RFIO as a 50-ohm controlled line over a continuous reference plane.
- Provide a conducted-test selection that cannot leave two RF paths connected.
- Provide a provisional antenna matching network adjacent to the antenna feed;
  populate values only after enclosure/body tuning.
- Keep the radio-to-test/antenna transition short and free of stubs.
- Define antenna keepout only after antenna choice and preserve it in board and
  enclosure CAD.
- Do not claim module certification: FGM230S is explicitly uncertified.

## Release gate

Pin/pad comparison, Figure 8.4 visual inspection, and independent dimensional
checking are complete. The footprint is not approved until KiCad parses both
native files without warnings, schematic ERC passes, and a second reviewer
signs the library report. PCB fabrication remains gated by the open RF,
power, audio, and mechanical evidence in the readiness checklist.
