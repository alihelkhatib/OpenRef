cmake_minimum_required(VERSION 3.22.0)

include(${SdkRootDirPath}/cmake/extension/mcux.cmake)

project(openref_rt595_benchmark LANGUAGES C CXX ASM
    PROJECT_BOARD_PORT_PATH
    ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec)

include(${SdkRootDirPath}/CMakeLists.txt)

get_filename_component(OPENREF_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../../.." ABSOLUTE)

mcux_add_source(BASE_PATH ${OPENREF_ROOT} SOURCES
    firmware/common/openref_audio_link.c
    firmware/audio_processor/common/openref_audio_capture.c
    firmware/audio_processor/common/openref_audio_playout.c
    firmware/audio_processor/common/openref_audio_mixer.c
    firmware/audio_processor/common/openref_audio_pipeline.c
    firmware/audio_processor/common/openref_audio_runtime.c
    firmware/audio_processor/benchmark/openref_audio_benchmark.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_lc3.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend_mcux.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_watchdog.c
    firmware/common/openref_audio_transport.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_spi.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_spi_mcux.c
    firmware/system/common/openref_update_verifier.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging_mcux.c
    firmware/system/common/openref_watchdog_gate.c
    firmware/audio_processor/targets/mimxrt595_evk/benchmark_target/openref_rt595_benchmark.c)

mcux_add_source(BASE_PATH ${SdkRootDirPath} SOURCES
    drivers/ctimer/fsl_ctimer.c
    drivers/wwdt/fsl_wwdt.c
    drivers/flexcomm/spi/fsl_spi.c
    drivers/flexcomm/spi/fsl_spi_dma.c
    examples/edgefast_bluetooth_examples/unicast_media_sender/modules/lc3_codec.c)

mcux_add_include(BASE_PATH ${OPENREF_ROOT} INCLUDES
    firmware/common
    firmware/audio_processor/common
    firmware/audio_processor/benchmark
    firmware/system/common
    firmware/audio_processor/targets/mimxrt595_evk
    firmware/audio_processor/targets/mimxrt595_evk/benchmark_target)

mcux_add_include(BASE_PATH ${SdkRootDirPath} INCLUDES
    drivers/ctimer
    drivers/flexcomm/spi
    ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec
    ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec/${core_id}
    examples/edgefast_bluetooth_examples/unicast_media_sender/modules
    middleware/wireless/ethermind/port/pal/mcux/lc3
    middleware/wireless/ethermind/port/pal/mcux/lc3/armgcc
    middleware/wireless/ethermind/bluetooth/private/utils/lc3
    middleware/wireless/ethermind/bluetooth/private/utils/lc3/private/fixed/config
    middleware/wireless/ethermind/bluetooth/private/utils/lc3/private/fixed/common
    middleware/wireless/ethermind/bluetooth/private/utils/lc3/export/include)

mcux_add_macro(CC
    "-DLC3_DSP=1 -DLC3_TEST_MODE=1 -DOPENREF_FIRMWARE_COMMIT=${OPENREF_FIRMWARE_COMMIT} -DOPENREF_BOARD_REVISION=${OPENREF_BOARD_REVISION} -DOPENREF_CURRENT_MEASUREMENT=${OPENREF_CURRENT_MEASUREMENT} -DOPENREF_IDLE_CURRENT_MA=${OPENREF_IDLE_CURRENT_MA} -DOPENREF_ONE_TALKER_CURRENT_MA=${OPENREF_ONE_TALKER_CURRENT_MA} -DOPENREF_SIX_TALKER_CURRENT_MA=${OPENREF_SIX_TALKER_CURRENT_MA}")

mcux_add_linker_symbol(SYMBOLS "__stack_size__=0x4000")

mcux_add_library(BASE_PATH ${SdkRootDirPath}/middleware/wireless/ethermind LIBS
    bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_encoder.a
    bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_decoder.a
    bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_common.a
    TOOLCHAINS armgcc CORES cm33)

mcux_convert_binary(BINARY ${APPLICATION_BINARY_DIR}/${MCUX_SDK_PROJECT_NAME}.bin)
