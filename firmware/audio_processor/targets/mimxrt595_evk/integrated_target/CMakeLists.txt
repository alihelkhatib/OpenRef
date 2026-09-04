cmake_minimum_required(VERSION 3.22.0)
include(${SdkRootDirPath}/cmake/extension/mcux.cmake)
project(openref_rt595_integrated LANGUAGES C CXX ASM PROJECT_BOARD_PORT_PATH ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec)
include(${SdkRootDirPath}/CMakeLists.txt)
get_filename_component(OPENREF_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../../.." ABSOLUTE)
mcux_add_source(BASE_PATH ${OPENREF_ROOT} SOURCES
 firmware/common/openref_audio_link.c firmware/common/openref_audio_transport.c
 firmware/audio_processor/common/openref_audio_capture.c firmware/audio_processor/common/openref_audio_playout.c
 firmware/audio_processor/common/openref_audio_mixer.c firmware/audio_processor/common/openref_audio_pipeline.c
 firmware/audio_processor/common/openref_audio_runtime.c
 firmware/audio_processor/benchmark/openref_audio_benchmark.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_lc3.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_spi.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_spi_mcux.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_io.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_audio_io_mcux.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_crypto.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_crypto_mcux.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator_mcux.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_coordinator.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_handoff.c
    firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_handoff_mcux.c
    firmware/system/common/openref_update_verifier.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_staging_mcux.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_delivery.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_output_guard.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_watchdog.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend_mcux.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state_mcux.c
 firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_app_confirmation.c
 firmware/system/common/openref_config_store.c firmware/system/common/openref_boot_policy.c
 firmware/system/common/openref_watchdog_gate.c
 firmware/audio_processor/targets/mimxrt595_evk/integrated_target/openref_rt595_integrated.c
 firmware/audio_processor/targets/mimxrt595_evk/integrated_target/openref_rt595_integrated_board.c)
mcux_add_source(BASE_PATH ${SdkRootDirPath} SOURCES drivers/ctimer/fsl_ctimer.c drivers/wwdt/fsl_wwdt.c drivers/dmic/fsl_dmic_dma.c drivers/flexcomm/spi/fsl_spi.c drivers/flexcomm/spi/fsl_spi_dma.c drivers/hashcrypt/fsl_hashcrypt.c middleware/mbedtls3x/library/asn1parse.c middleware/mbedtls3x/library/asn1write.c middleware/mbedtls3x/library/bignum.c middleware/mbedtls3x/library/bignum_core.c middleware/mbedtls3x/library/constant_time.c middleware/mbedtls3x/library/ecp.c middleware/mbedtls3x/library/ecp_curves.c middleware/mbedtls3x/library/ecdsa.c middleware/mbedtls3x/library/platform_util.c examples/edgefast_bluetooth_examples/unicast_media_sender/modules/lc3_codec.c)
mcux_add_include(BASE_PATH ${OPENREF_ROOT} INCLUDES firmware/common firmware/system/common firmware/audio_processor/common firmware/audio_processor/benchmark firmware/audio_processor/targets/mimxrt595_evk firmware/audio_processor/targets/mimxrt595_evk/integrated_target)
mcux_add_include(BASE_PATH ${SdkRootDirPath} INCLUDES drivers/ctimer drivers/dmic drivers/flexcomm/spi drivers/hashcrypt middleware/mbedtls3x/include middleware/mbedtls3x/library ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec ${board_root}/${board}/driver_examples/dmic/dmic_i2s_codec/${core_id} examples/edgefast_bluetooth_examples/unicast_media_sender/modules middleware/wireless/ethermind/port/pal/mcux/lc3 middleware/wireless/ethermind/port/pal/mcux/lc3/armgcc middleware/wireless/ethermind/bluetooth/private/utils/lc3 middleware/wireless/ethermind/bluetooth/private/utils/lc3/private/fixed/config middleware/wireless/ethermind/bluetooth/private/utils/lc3/private/fixed/common middleware/wireless/ethermind/bluetooth/private/utils/lc3/export/include)
if(NOT DEFINED OPENREF_LOCAL_SOURCE_ID OR OPENREF_LOCAL_SOURCE_ID LESS 1 OR OPENREF_LOCAL_SOURCE_ID GREATER 6)
  message(FATAL_ERROR "OPENREF_LOCAL_SOURCE_ID must be explicitly set to 1..6")
endif()
if(NOT DEFINED OPENREF_CURRENT_SLOT OR OPENREF_CURRENT_SLOT LESS 0 OR OPENREF_CURRENT_SLOT GREATER 1)
  message(FATAL_ERROR "OPENREF_CURRENT_SLOT must be explicitly set to 0 (A) or 1 (B)")
endif()
if(NOT DEFINED OPENREF_IMAGE_VERSION OR OPENREF_IMAGE_VERSION LESS 1)
  message(FATAL_ERROR "OPENREF_IMAGE_VERSION must be explicitly set to a positive signed-manifest version")
endif()
mcux_add_macro(CC "-DLC3_DSP=1 -DLC3_TEST_MODE=1 -DOPENREF_LOCAL_SOURCE_ID=${OPENREF_LOCAL_SOURCE_ID} -DOPENREF_CURRENT_SLOT=${OPENREF_CURRENT_SLOT} -DOPENREF_IMAGE_VERSION=${OPENREF_IMAGE_VERSION}")
if(DEFINED OPENREF_TRUST_ANCHOR_HEADER)
  if(NOT EXISTS "${OPENREF_TRUST_ANCHOR_HEADER}")
    message(FATAL_ERROR "OPENREF_TRUST_ANCHOR_HEADER does not exist")
  endif()
  get_filename_component(OPENREF_TRUST_DIR "${OPENREF_TRUST_ANCHOR_HEADER}" DIRECTORY)
  get_filename_component(OPENREF_TRUST_NAME "${OPENREF_TRUST_ANCHOR_HEADER}" NAME)
  if(NOT OPENREF_TRUST_NAME STREQUAL "openref_trust_anchor_generated.h")
    message(FATAL_ERROR "Trust anchor header must be named openref_trust_anchor_generated.h")
  endif()
  mcux_add_include(BASE_PATH "${OPENREF_TRUST_DIR}" INCLUDES .)
  mcux_add_macro(CC "-DOPENREF_HAS_TRUST_ANCHOR=1")
endif()
mcux_add_linker_symbol(SYMBOLS "__stack_size__=0x4000")
if(OPENREF_CURRENT_SLOT EQUAL 0)
  set(OPENREF_IMAGE_BASE 0x08041000)
else()
  set(OPENREF_IMAGE_BASE 0x08101000)
endif()
mcux_add_armgcc_linker_script(TARGETS flash_release BASE_PATH ${CMAKE_CURRENT_LIST_DIR}
  LINKER openref_rt595_slot.ld)
mcux_remove_armgcc_linker_script(TARGETS flash_release BASE_PATH ${SdkRootDirPath}
  LINKER ${device_root}/${soc_portfolio}/${soc_series}/${device}/gcc/${CONFIG_MCUX_TOOLCHAIN_LINKER_DEVICE_PREFIX}_flash.ld)
mcux_add_linker_symbol(SYMBOLS "OPENREF_IMAGE_BASE=${OPENREF_IMAGE_BASE} OPENREF_IMAGE_CAPACITY=0x000bf000")
mcux_add_library(BASE_PATH ${SdkRootDirPath}/middleware/wireless/ethermind LIBS bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_encoder.a bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_decoder.a bluetooth/private/lib/mcux/default/ble/cm33/gcc/libethermind_lc3_common.a TOOLCHAINS armgcc CORES cm33)
mcux_convert_binary(BINARY ${APPLICATION_BINARY_DIR}/${MCUX_SDK_PROJECT_NAME}.bin)
