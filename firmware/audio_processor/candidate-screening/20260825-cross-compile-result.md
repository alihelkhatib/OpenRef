# Audio Processor Cross-Compile Screen (2026-08-25)

## Conclusion

MIMXRT595, STM32H563, and the portable Apollo510 Cortex-M55 path pass the
no-hardware source-portability screen. None is promoted: this run did not link
LC3 or a vendor SDK and executed no target instructions.

ADSP-BF706/BF707 were not cross-compiled because they use the Blackfin+ ISA and
the required Analog Devices compiler is not installed. They remain eligible
for the identical vendor-operated benchmark request.

## Reproduction

The run used Arm GNU Toolchain 14.2.1 from the installed Silicon Labs toolchain:

```text
python tools/screen_audio_processor_candidates.py --compiler <path-to-arm-none-eabi-gcc>
```

All builds used C11, `-Os`, section splitting, warnings-as-errors, Thumb mode,
and soft floating-point ABI. The two Cortex-M33 profiles produced 3,726 bytes
of portable text sections; the Cortex-M55 profile produced 3,736 bytes. Data
and BSS sections in these relocatable portable objects were zero. These numbers
exclude LC3, platform startup, libraries, the linker, and target-specific code.

The generated machine-readable result and object files are kept under the
ignored `artifacts/local/audio-candidate-screen/` directory.

## Remaining admission evidence

For each candidate, the next free/low-cost action is a vendor- or
borrower-operated run using `vendor-run-request.md`. Required returns are the
paced result, raw log, ELF/map, stack high-water, and three current captures.
If a vendor supplies only an estimate, record it as an estimate and do not pass
the candidate.

Official tool/platform references:

- NXP MCUXpresso SDK RT595 documentation: <https://mcuxpresso.nxp.com/mcuxsdk/latest/html/boards/RT/evkmimxrt595/index.html>
- ST STM32H563 product page: <https://www.st.com/en/microcontrollers-microprocessors/stm32h563zi.html>
- Analog Devices CrossCore Embedded Studio: <https://www.analog.com/en/resources/evaluation-hardware-and-software/software/adswt-cces.html>
