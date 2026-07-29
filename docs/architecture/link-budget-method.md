# Link Budget Method

**Document ID:** OR-ARC-009  
**Revision:** 0.1  
**Status:** Analysis framework

## Purpose

Define a repeatable method for comparing candidate radios, antennas, frequencies, and body-worn placements.

## Core Model

The available receive margin is:

`Margin = P_TX + G_TX + G_RX - L_path - L_body - L_impl - S_RX`

Where:

- `P_TX` is conducted transmit power;
- `G_TX` and `G_RX` are realized antenna gains in the actual enclosure;
- `L_path` is propagation loss;
- `L_body` is body shadowing and detuning loss;
- `L_impl` includes cable, matching, enclosure, polarization, fading, and manufacturing losses;
- `S_RX` is receiver sensitivity at the selected data rate and error criterion.

## Required Loss Terms

Every candidate estimate shall explicitly include:

- free-space or measured field loss;
- near-body antenna efficiency;
- torso shadowing;
- polarization mismatch;
- orientation variation;
- enclosure and battery interaction;
- fading margin;
- adjacent-radio desensitization;
- implementation margin.

## Default Engineering Margins

Until measured data replaces them, calculations shall reserve separate allowances for:

| Source | Initial Allowance |
|---|---:|
| Manufacturing variation | 2 dB |
| Polarization and orientation | 3 dB |
| Fast fading | 6 dB |
| Body shadowing | 10 dB placeholder |
| Implementation uncertainty | 3 dB |

The body-shadowing placeholder is intentionally conservative and must be replaced with measurements.

## Measurement Geometry

Prototype tests shall include:

- same-side torso placement;
- opposite-side torso placement;
- front-to-back body shadow;
- referee-to-assistant across field width;
- diagonal corner-to-corner separation;
- kneeling or obstructed body posture;
- wet clothing;
- antenna near battery and headset cable;
- simultaneous motion.

## Acceptance Philosophy

The product shall not be designed to a zero-margin laboratory range.

The preferred architecture shall maintain positive link margin in the worst representative field geometry while supporting the required voice traffic and coexistence conditions.
