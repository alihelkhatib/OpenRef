# Voice Codec Trade Study

**Document ID:** OR-ARC-011  
**Revision:** 0.1  
**Status:** Evaluation plan

## Required Characteristics

The selected codec must provide:

- intelligible speech in wind and crowd noise;
- low algorithmic delay;
- moderate bitrate;
- bounded CPU and memory use;
- resilience to packet loss;
- implementation licensing compatible with an open product;
- deterministic operation on the selected embedded platform.

## Candidate Classes

### Narrowband Speech Codec

Advantages:

- low bitrate;
- low radio airtime;
- modest processing.

Disadvantages:

- reduced consonant clarity;
- less natural speech;
- weaker robustness when several voices overlap.

### Wideband Speech Codec

Advantages:

- improved intelligibility;
- better differentiation of overlapping voices;
- more natural monitoring.

Disadvantages:

- higher bitrate;
- greater processing and memory demands.

### General-Purpose Low-Delay Audio Codec

Advantages:

- strong quality;
- flexible rate and packet-loss features.

Disadvantages:

- potentially excessive complexity;
- licensing or implementation concerns;
- may require more capable hardware than necessary.

## Evaluation Points

Each candidate shall be tested at:

- 10 ms and 20 ms packetization;
- 16, 24, and 32 kbps where supported;
- 0%, 5%, 10%, 20%, and burst packet loss;
- single speaker;
- two simultaneous speakers;
- five simultaneous remote speakers;
- representative wind and crowd recordings.

## Selection Rule

Codec selection shall be based on intelligibility, latency, resource use, packet-loss behavior, and legal suitability.

Perceived fidelity alone is not sufficient.
