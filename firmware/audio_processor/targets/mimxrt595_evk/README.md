# MIMXRT595-EVK Audio Validation Target

This directory is the target boundary for the first complete OpenRef audio
bench. The portable pipeline and runtime are ready; MCUXpresso-generated clock,
pin, DMA, DMIC, WM8904, and Flexcomm files belong here after the board and SDK
are available.

## Reproducible SDK and toolchain setup

The command-line baseline is NXP MCUXpresso SDK `v26.06.00-LTS`, pinned to
manifest commit `b01ab9032249f0d10cf6791ee4d7de45dfb19166`. It uses NXP's
board-targeted West download for `evkmimxrt595`, rather than the 7-8 GB
all-board workspace. On Windows, install the complete local baseline with:

```powershell
powershell -ExecutionPolicy Bypass -File tools/setup_rt595_sdk.ps1 -BuildSmokeTest
```

The script installs pinned West 1.5.0, CMake 3.31.6, Ninja 1.13.0,
jsonschema 4.25.1, and Arm GNU
Toolchain 14.3.Rel1 under ignored `artifacts/local/` paths. It verifies the Arm
archive against the publisher's SHA-256
`864c0c8815857d68a1bbba2e5e2782255bb922845c71c97636004a3d74f60986`
before extraction and rejects a manifest checkout that does not match the
pinned commit. Re-run with `-SkipSdkUpdate` for an offline verification of an
existing workspace.

After setup, set `ARMGCC_DIR` to `artifacts/local/rt595-toolchain` and prepend
the SDK virtual environment and `$env:ARMGCC_DIR\bin` to `PATH`. Raw SDK files,
toolchains, build outputs, and license-bearing middleware stay untracked.

Compile and link the portable OpenRef audio pipeline against the installed
RT595 board support package with:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_rt595_openref_smoke.ps1 -Pristine
```

The smoke application links NXP's SDK-shipped EtherMind Cortex-M33 LC3 binary
through the BSD-licensed wrapper used by NXP's Bluetooth audio examples. It
creates one 16 kHz/10 ms/40-byte encoder and five independent decoders and runs
four portable benchmark blocks, including one forced PLC decode. The image
reports success only when the benchmark completes with zero codec/process
failures and observes PLC. It is deliberately not promotion firmware: its
clock is synthetic and it has no DMA pacing. It proves the codec ABI, board
startup, portable-source inclusion, complete static allocation, and final link
before real DMA and timing callbacks are introduced. The EtherMind libraries
remain inside the ignored SDK installation and are not redistributed here.

## Paced promotion target

`benchmark_target/` is the separate measurement image. Build it in release
configuration with `tools/build_rt595_openref_benchmark.ps1 -Pristine`. CTIMER2
generates an interrupt every 10 ms and the main loop consumes exactly one tick
per benchmark step; CTIMER0 is an independent, free-running 1 MHz 32-bit timing
source. The image uses the canonical 1,000 warmup and 180,000 measured blocks,
reports pacing overruns, watermarks a 16 KiB bare-metal stack, and emits one
validator-shaped JSON object on the debug UART.

The build defaults current fields to `null`, so an unmeasured result correctly
fails promotion validation. Supply measured values and a measurement-method
description through the build script only after collecting them on the same
board configuration. A successful cross-build proves compilation and linkage,
not 10 ms pacing, execution time, stack use, current, or benchmark passage;
those require flashing the board and preserving its raw UART log.

For an instrumented board run, install
[NXP LinkServer](https://www.nxp.com/design/design-center/software/development-software/mcuxpresso-software-and-tools-/linkserver-for-microcontrollers%3ALINKSERVER)
(the West default; tested route is Windows revision 26.6.137) or SEGGER J-Link,
build with the measured current fields, identify the EVK's debug UART with
`python tools/capture_serial.py --list`, then run:

```powershell
powershell -ExecutionPolicy Bypass -File tools/run_rt595_openref_benchmark.ps1 `
  -Port COM7 -Runner linkserver
```

The capture starts before flashing so the startup banner is not lost. The
canonical workload lasts 1,810 seconds (1,000 warmup plus 180,000 measured
10 ms blocks), so the wrapper enforces at least a 1,830-second capture and
defaults to 1,860 seconds. It preserves the raw UART log, ELF, linker map,
capture diagnostics, and hashes in an ignored dated directory; extracts the
single schema-tagged JSON line; and runs the promotion validator. Use
`-SkipFlash` only when the same ELF has already been flashed, and reset the
board when prompted. A run with `null` current fields, pacing overruns,
failures, deadline misses, or a total maximum above 8 ms fails validation.

The paced image enables RT595 WWDT0 from the independent low-power oscillator
with a 250 ms reset timeout. A one-task `openref_watchdog_gate` evaluates the
previous successful block before accepting new progress and permits a hardware
refresh only when the processing loop has progressed within 50 ms. Once the
gate observes stale progress, the image deliberately stops refreshing WWDT0.
The cross-build verifies that the SDK clock, WWDT reset configuration, gate,
and refresh path are linked; it does not prove timeout accuracy or physical
reset behavior. Before promotion, deliberately stop progress after watchdog
initialization on an EVK and preserve UART, reset-cause, and elapsed-time
evidence showing a watchdog reset near 250 ms.

`openref_rt595_config_backend` is the dedicated persistent-configuration seam;
it is intentionally separate from firmware-update storage. Each 80-byte
`openref_config_store` record occupies its own erase sector, and writes erase
only the inactive slot's sector, program one aligned page padded with `0xff`,
then read back and compare the record. Initialization rejects unaligned
geometry, ranges outside flash, config regions below the protected firmware
end, or fewer than two complete sectors. The RT595 EVK geometry used by the
native fake-driver test is a 256-byte page and 4 KiB sector, with two sectors
provisionally allocated at `0x081fc000..0x081fe000`; the following two sectors
are reserved for boot state. The integrated link-map gate limits the current
XIP image to `0x08000000..0x08040000`, and the final IAP
binding must pass the linked image end as `protected_end`; do not enable writes
until the linker map proves this reservation. Physical erase/program,
power-loss, cache invalidation, and endurance behavior remain unvalidated.

The target defines `LC3_TEST_MODE`, matching the setting embedded in NXP's
prebuilt LC3 objects; in this SDK it selects the codec's standalone fixed-width
types and avoids importing EtherMind's FreeRTOS `EM_os.h` into the bare-metal
smoke application. It does not substitute a codec stub or test algorithm.

## Integrated application target

`integrated_target/` is a separate, slot-linked application composition image.
Build it with `tools/build_rt595_openref_integrated.ps1 -LocalSourceId 1
-CurrentSlot A -ImageVersion 1 -Pristine`. The slot and image version are
mandatory release inputs and must match the signed manifest. The custom linker
places the vector table at the selected candidate-image base and bounds all
flash VMAs and LMAs to that slot; the build validates the resulting map against
the same canonical layout. Its reachable main
loop initializes the LC3 runtime, the DMIC/I2S DMA seam, SPI-peripheral DMA
transport, CTIMER timing, and gated WWDT; it drains remote frames before each
160-sample block, processes microphone audio, queues the local LC3 frame, and
submits mono output through the stereo I2S adapter. DMA0 is initialized once by
the application before either adapter claims channels, avoiding destructive
double initialization.

The checked-in integrated target includes a concrete EVK board port for DMIC0,
I2S3, WM8904 at 16 kHz, SPI5, `AUDIO_REQn`, and non-overlapping DMA0 channels.
It applies a conservative codec volume and requires a synchronous physical mute
before audio initialization. The build also requires an explicit provisioned
local source ID in the inclusive range 1 through 6; a missing, zero, or
out-of-range identity fails before the audio runtime starts. The weak defaults
remain fail-closed so removing or failing to link the board port cannot silently
produce a permissive image. The current ELF proves source inclusion, resource
allocation, and link reachability, but is not an on-board audio result. Do not
claim live audio until clock, pin, DMA IRQ, mute, and reset behavior are
preserved as physical evidence.

The application opens the boot-state IAP backend only when both VTOR and its
own code address are inside the slot selected at build time. It loads the two
protected boot-state sectors and starts the 30-second confirmation soak only
when that durable state names this slot as an attempted, still-pending trial.
Each successful 10 ms audio block samples the live clock, storage, watchdog,
DMA/output, peer-status, and transport-fault signals. Any unhealthy sample
restarts the soak; only a complete healthy soak may clear the pending slot and
advance the anti-rollback floor. Confirmed boots, wrong-slot/development images,
and malformed or unreadable state cannot write confirmation records.

The setup smoke test builds NXP's `hello_world` for the Cortex-M33 debug
configuration. The audio-board baseline can be compiled separately from the
generated `workspace/mcuxsdk` directory with:

```powershell
west build -p always examples/driver_examples/dmic/dmic_i2s_codec `
  --toolchain armgcc --config flash_debug -b evkmimxrt595 `
  -Dcore_id=cm33
```

## Starting SDK example

Begin from NXP's `dmic_i2s_codec` example for EVK-MIMXRT595. It already proves
the onboard DMIC-to-WM8904 path. Preserve its clock and codec initialization,
replace its PCM copy loop with 160-sample ping-pong DMA blocks, and invoke
`openref_audio_runtime_process()` once for every completed 10 ms capture block.
Use 16 kHz, signed 16-bit, mono processing internally; duplicate the limited
mono result into both codec channels only at the playback boundary.

The official audio demo requires headphones on J4 and documents jumpers JP7,
JP8, JP27, JP28, and JP29 in positions 1-2. Confirm the actual board revision
and jumper labels before applying power.

## Processor-link bench wiring

The FG23 remains the SPI controller. The RT595 target is a full-duplex SPI
peripheral with one active-low request output. Use an exposed RT595 Flexcomm or
PMOD SPI instance and keep all signals at 3.3 V logic.

For BRD2600A, the provisional non-debug pin allocation is:

| Link signal | FG23 breakout | FG23 role |
|---|---|---|
| COPI | PA7, pad 12 | SPI controller output |
| CIPO | PA8, pad 13 | SPI controller input |
| SCLK | PB0, pad 14 | SPI controller clock |
| CSn | PB1, pad 10 | SPI controller select |
| AUDIO_REQn | PB2, pad 11 | GPIO input |
| AUDIO_RESETn | PB3, pad 15 | GPIO output |
| Ground | GND, pad 17 | Common reference |

Disable the BRD2600A Si7021, LC sensor, button 0, and LED before assigning these
pins. Do not use PA1 or PA2 for this link: they are SWCLK and SWDIO, and must
remain available for programming and debug. The existing PA1/PA2/PB2/PB3 scope
wires are test instrumentation, not all four SPI wires.

During initial bring-up, power both boards independently from USB and connect
only the common ground and logic signals. Do not join 5 V, 3.3 V, or VMCU rails.
Add 22-47 ohm source-series resistance on SCLK and COPI if edge ringing is
visible; the production schematic retains configurable series footprints.

### RT595 SPI/DMA firmware seam

`openref_rt595_audio_spi.c` implements the processor-neutral peripheral state
machine. It always arms an exact 98-byte full-duplex transaction, sends a valid
idle status when no application frame is pending, gives queued audio priority,
and asserts `AUDIO_REQn` only while application data is pending or already in
the armed transaction. DMA callbacks only publish completion state; CRC decode,
queue mutation, and re-arming occur from `openref_rt595_audio_spi_poll()`.
Short, failed, duplicate, and malformed transfers are discarded and counted.
`openref_rt595_audio_spi_reset()` aborts the in-flight DMA and clears stale
transport state before deasserting the request line.

`openref_rt595_audio_spi_mcux.c` binds that seam to an MCUX SPI peripheral and
two LPC DMA channels. The integrated EVK port supplies `SPI5`, `DMA0`, RX
channel 10, TX channel 11, the SPI5 clock and pin mux, and active-low
`AUDIO_REQn` on PIO1_14/J36 pin 1. Other boards must provide equivalent,
validated resource and connector assignments. Native tests exercise state
transitions and failure handling; a successful cross-build proves SDK API
compatibility only, not electrical operation.

### Inactive update-slot staging

The canonical provisional 2 MiB FlexSPI layout is machine-readable in
`openref_rt595_flash_layout.json`. It reserves 256 KiB for the bootloader or
the current development integrated XIP image, then two equal slots containing
one 4 KiB signed-manifest commit sector plus 764 KiB image capacity, followed
by reserved scratch, two configuration sectors, and two boot-state sectors.
`tools/validate_rt595_flash_layout.py` rejects gaps, overlaps, arithmetic
overflow, alignment errors, asymmetric candidates, non-writable manifest
commit sectors, and a
linked image whose VMA or flash load address escapes the protected XIP region.
The integrated build runs this check against `output.map` before reporting an
ELF. This is a provisional software allocation, not evidence that ROM remap,
slot execution, or power-cut-safe activation works on hardware.

`openref_rt595_update_staging.c` couples an already-started portable update
verifier to a bounded inactive flash region. It rejects invalid geometry and
oversized manifests, erases only the configured region, accepts arbitrary input
chunks into page-sized writes, verifies every programmed page by reading it
back, and never changes boot state. Any hash, erase, program, or verify failure
ends the session fail-closed. The MCUX binding uses aligned buffers with the ROM
FlexSPI NOR IAP calls. Production addresses must come from an authoritative
bootloader/linker layout; activation, cache/XIP safety, reset-time slot
authentication, rollback records, and physical power-cut recovery remain
unvalidated. Cross-building this code does not execute a flash operation.

The inactive slot's manifest sector is erased before image staging and remains
invalid throughout the transfer. After every image page has been programmed,
read back, and hashed, the stager commits the original signature-verified
144-byte manifest as the final page write and verifies that page. A reset-time
bootloader must still read that manifest and re-authenticate the complete image;
the manifest is a commit record, never a substitute for boot-time verification.

`openref_rt595_update_delivery.c` is the bounded application receiver above
that staging layer. An authenticated and authorized command demultiplexer
supplies a 144-byte signed manifest, chunks of at most 512 bytes, and a finish
command. The receiver accepts only a monotonically increasing nonzero session,
targets only the slot other than the executing image, authenticates the
manifest before erase, and requires every chunk's session, sequence, and byte
offset to be exact. Duplicate, reordered, oversized, overflowing, conflicting,
timed-out, and reset transactions abort without publishing a manifest.

After image readback authentication and the manifest-last commit, a separate
durable boot-state update makes the candidate trial-eligible. If that state
write fails, a valid inactive image may remain but is not selected. Replay
memory is boot-local; after power loss, the manifest commit boundary and signed
version/boot-state floor remain authoritative. The functions declared in
`integrated_target/openref_rt595_integrated_update.h` are a narrow trusted
application boundary, not a raw SPI parser, and must only be called after the
upstream command channel has authenticated and authorized its peer.

### 10 ms audio I/O DMA ownership

`openref_rt595_audio_io.c` owns two 160-sample signed-16-bit mono buffers in
each direction. DMA completion immediately rearms capture, drops the oldest
unconsumed capture block on overrun, selects a prepared playout block, and
substitutes silence on underrun. Counters expose completed blocks, overruns,
underruns, and DMA failures. The MCUX binding uses the EVK example's DMA0 DMIC
RX channel 16 and I2S3 TX channel 7, and the integrated target keeps its symbols
live. A successful build does not prove 16 kHz clocks, analog routing, or
channel mapping; validate each on the physical board before audible testing.

The installed EVK ports expose one important conflict: the debug console owns
Flexcomm0 (`USART0`), while NXP's DMIC/I2S example also initializes `I2S0`.
Production playout therefore uses the example's already-routed Flexcomm3 data
output (PIO0_23, package C13) and attaches the audio PLL to Flexcomm3; it must
not reconfigure Flexcomm0 while diagnostic UART is live. SPI5 uses the SDK
slave-example route PIO1_3/4/5/6 (SCK/CIPO/COPI/SSEL0), which is disjoint from
I3C0 PIO2_29/30/31, DMIC PIO5_4/8, MCLK PIO1_10, and the I2S bridge pins
PIO0_7/8/9/23. DMA channels 7, 10, 11, and 16 are reserved respectively for
I2S TX, SPI RX, SPI TX, and DMIC RX. Compile-time checks in
`openref_rt595_board_resources.h` reject Flexcomm/DMA collisions and clock
divider drift.

The stock example is 48 kHz: audio PLL / 8 feeds DMIC 2fs/OSR32 and its I2S
divider is 16. The concrete 16 kHz port uses DMIC divider 24/OSR32, I2S3
divider 48, WM8904 16 kHz format, and a conservative headphone volume of 20.
SPI5 is exposed at JP26 (pins 4/3/2/1 are SCK/CIPO/COPI/SSEL0). Active-low
`AUDIO_REQn` uses otherwise-unused PIO1_14 at J36 pin 1; J36 pin 9 is ground.
No `AUDIO_RESETn` is required by the current transport seam. These settings
compile against the pinned SDK but remain electrically unvalidated.

Build with an explicit node identity from 1 through 6:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_rt595_openref_integrated.ps1 -LocalSourceId 1 -Pristine
```

### Update signature crypto

`openref_rt595_update_crypto.c` adapts a fixed eight-byte key ID and fixed
64-byte P-256 public point (`X || Y`) to the portable verifier. The anchor is
copied once at initialization; zero anchors, unknown IDs, hash failures,
off-curve points, invalid raw `r || s` signatures, and driver failures reject
the update. The MCUX backend uses RT595 HASHCRYPT streaming SHA-256 and a
minimal build of the SDK-shipped Mbed TLS 3.x P-256 verifier. CASPER exposes
curve primitives but no complete driver-level ECDSA verification contract, so
custom signature arithmetic was intentionally not introduced. No private key
or restricted source is included. Production still needs an approved trust
anchor, signed known-answer vectors, key rotation/revocation policy,
accelerator concurrency rules, and on-silicon fault testing; cross-build success
is not cryptographic hardware evidence.

`openref_rt595_slot_authenticator.c` is the boot-policy boundary for an
inactive candidate. Each slot supplies separate manifest and image bases, so
the authoritative 4 KiB manifest-sector reservation and image-at-`+0x1000`
layout are not collapsed into an inline 144-byte prefix. It rejects the running
slot and invalid/overlapping region geometry, reads the immutable 144-byte manifest, delegates target, hardware,
bootloader, rollback, version, signature, and declared-size policy to the
portable verifier, then streams exactly the declared image from flash in
256-byte chunks. Only a completed digest match returns a present/authenticated
slot and version; every failure leaves the output unauthenticated. The MCUX
binding uses aligned buffers with ROM FlexSPI NOR reads. It never erases,
programs, changes boot records, or jumps to a vector. Native tests cover image
mutation, truncated reads, the running/wrong slot, overlapping ranges, and
rollback rejection.

## Bring-up sequence

### Durable boot state (not an activator)

`openref_rt595_boot_state` transactionally persists the boot policy's confirmed
slot, pending slot, trial count, and anti-rollback minimum in alternating
CRC-protected records. A trial attempt is returned only after its increment is
durable; failed erase/program/readback therefore returns no boot decision and
keeps the prior in-memory state. Stage and confirmation similarly roll back in
RAM when persistence fails. The MCUX adapter uses the same bounded, aligned,
full-page IAP backend and readback checks as configuration storage, but must be
given two dedicated sectors outside code, configuration, and update-slot ranges.

This code deliberately provides no automatic slot activation or boot-ROM
integration. Those operations remain disabled until the immutable bootstrap
owns slot verification and the memory map.
Native tests simulate interrupted writes and corrupt readback; physical
erase/program power cuts, cache behavior after brownout, and endurance remain
unvalidated on the EVK.

`openref_rt595_app_confirmation` is the application-side trial supervisor. It
can start only when the durable record says the authenticated running slot is
pending and has already consumed a trial attempt. The application must submit
one health observation per completed 10 ms audio block, with a monotonic
millisecond timestamp. Zero-time or greater-than-20-ms gaps invalidate the
continuity proof. Confirmation requires
3,000 consecutive observations (30 seconds) with clocks, storage, watchdog,
audio processing, peer status, and the global fault state all healthy. Any bad
observation or application fault clears the soak; reset clears it naturally
because progress is deliberately RAM-only. Confirmation uses the transactional
boot-state store, and failed persistence clears progress and leaves the old
confirmed slot and pending trial intact. A recovered store must pass a new full
soak before retry. The portable test exercises each health input, fault/reset
semantics, stale/non-trial rejection, and failed-write recovery. Target
compilation is not evidence that the application has wired every health source
or survived the soak on the EVK.

`openref_rt595_boot_coordinator` composes reset-time authentication with this
durable state. It authenticates both candidates from the immutable bootstrap,
interprets the persisted minimum version as an inclusive rollback floor (so
the confirmed image remains eligible), and invokes the durable selector only
after both full images have been checked. A failed candidate is represented as
ineligible rather than preventing fallback to the other slot. Missing boot
state returns no decision. A selection result alone never permits a jump, and
the handoff validator rejects a layout not explicitly marked authenticated.
`openref_rt595_boot_handoff` separately reads and validates the selected
image's vector table: the VTOR base must meet a caller-supplied power-of-two
alignment of at least 128 bytes, MSP must be 8-byte aligned and inside the
declared RAM range (the top-of-RAM value is allowed), and the reset vector must
be a Thumb address inside the authenticated image after its vector words.
Failure clears the portable plan.

The MCUX binding disables interrupts and SysTick, disables and clears every
implemented NVIC line, clears pending SysTick/PendSV state, cleans and disables
both RT595 CACHE64 controllers, installs VTOR, executes DSB/ISB, and sets MSP plus
branches in one assembly transaction. An invalid plan or impossible interrupt
bank count enters a masked WFI loop. Portable tests prove the teardown ordering
and injected-failure behavior; the target source is included in the pinned SDK
build. The independent `bootstrap_target` supplies the authenticated manifest's
exact image size (never the whole slot capacity), RT595 application RAM bounds,
and a conservative VTOR alignment. It requires durable state and a generated
trust anchor; missing/corrupt state, failed authentication, no eligible slot,
invalid vectors, or an unexpectedly returning reset handler all enter a masked
WFI recovery loop without trying another unauthenticated path. Build it with:

When the confirmed slot is invalid but the alternate is fully authenticated,
the coordinator first persists that alternate as a normal bounded trial and
persists its attempt increment before handoff. If its attempt budget is
exhausted while the confirmed slot remains unusable, the exhausted pending
record is retained as a recovery latch; resets cannot clear and restage it.
Missing or corrupt durable state is never reconstructed from slot metadata,
because doing so would discard the stored anti-rollback floor. Recovery writes
`0x4f520000 | reason` to RTC `GPREG[0]` and a saturating recovery/reset count to
`GPREG[1]`. These debugger/service-readable words are status-only and confer no
boot or flash-write authority. Flash-read failure, missing state, no
authenticated image, policy exhaustion, vector rejection, and an unexpected
return have distinct reason values.

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_rt595_openref_bootstrap.ps1 `
  -TrustAnchorHeader artifacts\local\trust\openref_trust_anchor_generated.h `
  -Pristine
```

The wrapper validates every flash-resident map section against the immutable
`bootstrap_xip` partition. Cross-compilation is not board evidence: cold/warm
handoffs, pending interrupts, enabled caches, malformed vectors, and watchdog
fallback remain physical promotion tests. In particular, RTC retention across
brownout and watchdog-reset causes must be confirmed on the EVK. The bootstrap
has not been flashed.

### Trust-anchor provisioning

Blank-device initialization is mediated by `openref_rt595_factory_provisioning`.
It requires a target-supplied physical manufacturing authorization signal and
classifies configuration, boot-state, and identity/trust-metadata regions as
blank, matching, other-valid, corrupt, or unreadable. It has deliberately no
erase operation. Configuration and boot state are programmed and read back
before the identity/trust metadata commit record; an irreversible target lock
is set and read back last. An interrupted run may resume only across blank or
byte-for-byte matching regions. Foreign valid data, corruption, I/O ambiguity,
failed readback, or a locked mismatch fails closed.

The physical jig challenge/strap, device-unique identity source, OTP/PFR lock
binding, canonical record construction, and production key custody remain
controlled factory integrations and require sacrificial-EVK validation. This
repository contains no production identity or secret, and compilation is not
evidence that a device was provisioned.

No production update key is stored in this repository or selected by default.
Provisioning accepts only an unencrypted PEM `PUBLIC KEY` containing a P-256
SubjectPublicKeyInfo; private-key PEM, other curves, compressed points,
off-curve points, malformed DER, and trailing data are rejected. Generate the
firmware header and auditable JSON manifest outside the source tree:

```powershell
python tools/provision_rt595_trust_anchor.py `
  --public-key C:\secure\openref-update-public.pem `
  --header artifacts\local\trust\openref_trust_anchor_generated.h `
  --manifest artifacts\local\trust\openref_trust_anchor.json
powershell -ExecutionPolicy Bypass -File tools/build_rt595_openref_integrated.ps1 `
  -LocalSourceId 1 `
  -TrustAnchorHeader artifacts\local\trust\openref_trust_anchor_generated.h `
  -Pristine
```

The stable eight-byte key ID is the first eight bytes of SHA-256 over raw
big-endian `X || Y`. The manifest records that derivation plus SHA-256 of both
the raw point and canonical input SPKI DER. Treat the generated header as
controlled release input: independently compare its hashes with the manifest
before signing or flashing a production image.

### Signed slot packaging

`tools/package_rt595_signed_slot.py` is the release-side counterpart to the
bootstrap verifier. It reads the canonical flash-layout JSON and emits one
binary beginning at the selected slot's manifest-sector base: the exact
144-byte manifest, erased `0xff` padding through byte 4095, then the exact
application image. It never generates or exports a private key. Signing accepts
only an external, unencrypted PKCS#8 P-256 key and uses deterministic RFC 6979
ECDSA with a canonical low-S, fixed-width, big-endian `r || s` signature.

The 80 signed bytes are `ORUP`, format version 1, audio target 2, two reserved
zero bytes, little-endian hardware ID/image version/minimum bootstrap
version/image byte count, SHA-256 of the exact image, a nonzero 16-byte release
ID, and the first eight bytes of SHA-256 over raw public-key `X || Y`. The
independent `verify` command rechecks the signature and hash plus slot capacity,
sector padding, hardware ID, installed bootstrap version, antirollback floor,
and the strict `image_version > confirmed_image_version` rule used by firmware.

```powershell
python tools/package_rt595_signed_slot.py pack `
  --layout firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_flash_layout.json `
  --slot A --image C:\release\openref-app.bin `
  --private-key C:\secure\openref-update-private.pem `
  --image-version 2 --minimum-bootloader-version 1 `
  --maximum-bootloader-version 1 `
  --antirollback-floor 1 --confirmed-image-version 1 `
  --release-id 00112233-4455-6677-8899-aabbccddeeff `
  --output artifacts\local\release\slot-a-v2.bin

python tools/package_rt595_signed_slot.py verify `
  --layout firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_flash_layout.json `
  --slot A --package artifacts\local\release\slot-a-v2.bin `
  --public-key C:\secure\openref-update-public.pem `
  --bootloader-version 1 --antirollback-floor 1 `
  --confirmed-image-version 1
```

The adjacent deterministic JSON record binds the slot addresses, versions,
sizes, key ID, and SHA-256 values. Keep the production private key outside the
repository and build directory. The deterministic scalar used by unit tests is
created only inside pytest's temporary directory and must never be provisioned.

1. Run the unmodified NXP DMIC-to-headphone example and verify clean local
   loopback at conservative headphone volume.
2. Convert the example to 160-sample ping-pong DMA and verify exactly 100 block
   completions per second with no overrun.
3. Integrate the portable runtime with a deterministic codec stub; require zero
   deadline misses for 30 minutes.
4. Integrate one LC3 encoder and five decoder states. Log maximum encode,
   render, and total times; total must remain at or below 8 ms.
5. Add 8 MHz SPI and exchange the fixed 98-byte frame. Inject CRC corruption,
   sequence gaps, processor reset, and queue overflow.
6. Run microphone-to-radio and radio-to-headphone simultaneously for one hour,
   then repeat with five remote sources and forced packet loss.
7. Measure idle, local loopback, one-talker, and six-talker current before
   promoting the processor choice.

## Promotion evidence

Store serial logs, firmware hashes, SDK version, board revision, jumper state,
timing maxima, stack high-water, and current captures under an ignored dated
artifact directory. Summarize the reproducible result in a tracked Markdown
report; do not promote the platform from an audible-only demonstration.

Official references:

- <https://www.nxp.com/design/design-center/development-boards-and-designs/i-mx-evaluation-and-development-boards/i-mx-rt595-evaluation-kit%3AMIMXRT595-EVK>
- <https://mcuxpresso.nxp.com/mcuxsdk/latest/html/examples/driver_examples/dmic/dmic_i2s_codec/readme.html>
- <https://www.silabs.com/documents/public/user-guides/ug508-brd2600a-user-guide.pdf>
