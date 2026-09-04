cmake_minimum_required(VERSION 3.22.0)

include(${SdkRootDirPath}/cmake/extension/mcux.cmake)

project(openref_rt595_smoke LANGUAGES C CXX ASM
    PROJECT_BOARD_PORT_PATH
    ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec)

include(${SdkRootDirPath}/CMakeLists.txt)

get_filename_component(OPENREF_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../../.." ABSOLUTE)

mcux_add_source(
    BASE_PATH ${OPENREF_ROOT}
    SOURCES
        firmware/common/openref_audio_link.c
        firmware/audio_processor/common/openref_audio_capture.c
        firmware/audio_processor/common/openref_audio_playout.c
        firmware/audio_processor/common/openref_audio_mixer.c
        firmware/audio_processor/common/openref_audio_pipeline.c
        firmware/audio_processor/common/openref_audio_runtime.c
        firmware/audio_processor/benchmark/openref_audio_benchmark.c
        firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_lc3.c
        firmware/audio_processor/targets/mimxrt595_evk/smoke/openref_rt595_smoke.c
)

mcux_add_source(
    BASE_PATH ${SdkRootDirPath}
    SOURCES
        examples/edgefast_bluetooth_examples/unicast_media_sender/modules/lc3_codec.c
)

mcux_add_include(
    BASE_PATH ${OPENREF_ROOT}
    INCLUDES
        firmware/common
        firmware/audio_processor/common
        firmware/audio_processor/benchmark
        firmware/audio_processor/targets/mimxrt595_evk
        firmware/audio_processor/targets/mimxrt595_evk/smoke
)

mcux_add_include(
    BASE_PATH ${SdkRootDirPath}
    INCLUDES
        ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec
        ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec/${core_id}
        examples/edgefast_bluetooth_examples/unicast_media_sender/modules
        middleware/wireless/ethermind/port/pal/mcux/lc3
        middleware/wireless/ethermind/port/pal/mcux/lc3/armgcc
        middleware/wireless/ethermind/bluetooth/private/utils/lc3
        middleware/wireless/ethermind/bluetooth/private/utils/lc3/private/fixed/config
        middleware/wireless/ethermind/bluetooth/private/utils/lc3/private/fixed/common
        middleware/wireless/ethermind/bluetooth/private/utils/lc3/export/include
)

# The smoke image consumes only the standalone LC3 API. LC3_TEST_MODE selects
# the codec's self-contained fixed-width types instead of dragging the full
# EtherMind/FreeRTOS OS abstraction into this bare-metal target.
mcux_add_macro(CC "-DLC3_DSP=1 -DLC3_TEST_MODE=1")

mcux_add_library(
    BASE_PATH ${SdkRootDirPath}/middleware/wireless/ethermind
    LIBS
        bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_encoder.a
        bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_decoder.a
        bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_common.a
    TOOLCHAINS armgcc
    CORES cm33
)

mcux_convert_binary(BINARY ${APPLICATION_BINARY_DIR}/${MCUX_SDK_PROJECT_NAME}.bin)
