cmake_minimum_required(VERSION 3.22.0)
include(${SdkRootDirPath}/cmake/extension/mcux.cmake)
project(openref_rt595_bootstrap LANGUAGES C CXX ASM
  PROJECT_BOARD_PORT_PATH ${board_root}/${board}/driver_examples/iap/flash_fcb)
include(${SdkRootDirPath}/CMakeLists.txt)
get_filename_component(OPENREF_ROOT "${CMAKE_CURRENT_LIST_DIR}/../../../../.." ABSOLUTE)

if(NOT DEFINED OPENREF_TRUST_ANCHOR_HEADER OR
   NOT EXISTS "${OPENREF_TRUST_ANCHOR_HEADER}")
  message(FATAL_ERROR "The immutable bootstrap requires OPENREF_TRUST_ANCHOR_HEADER")
endif()
get_filename_component(OPENREF_TRUST_DIR "${OPENREF_TRUST_ANCHOR_HEADER}" DIRECTORY)
get_filename_component(OPENREF_TRUST_NAME "${OPENREF_TRUST_ANCHOR_HEADER}" NAME)
if(NOT OPENREF_TRUST_NAME STREQUAL "openref_trust_anchor_generated.h")
  message(FATAL_ERROR "Trust anchor header must be named openref_trust_anchor_generated.h")
endif()

mcux_add_source(BASE_PATH ${OPENREF_ROOT} SOURCES
  firmware/system/common/openref_config_store.c
  firmware/system/common/openref_boot_policy.c
  firmware/system/common/openref_update_verifier.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_crypto.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_update_crypto_mcux.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_slot_authenticator_mcux.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_state_mcux.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_config_backend_mcux.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_factory_provisioning.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_coordinator.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_handoff.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_boot_handoff_mcux.c
  firmware/audio_processor/targets/mimxrt595_evk/openref_rt595_bootstrap.c
  firmware/audio_processor/targets/mimxrt595_evk/bootstrap_target/openref_rt595_bootstrap_main.c)
mcux_add_source(BASE_PATH ${SdkRootDirPath} SOURCES
  drivers/hashcrypt/fsl_hashcrypt.c
  middleware/mbedtls3x/library/asn1parse.c
  middleware/mbedtls3x/library/asn1write.c
  middleware/mbedtls3x/library/bignum.c
  middleware/mbedtls3x/library/bignum_core.c
  middleware/mbedtls3x/library/constant_time.c
  middleware/mbedtls3x/library/ecp.c
  middleware/mbedtls3x/library/ecp_curves.c
  middleware/mbedtls3x/library/ecdsa.c
  middleware/mbedtls3x/library/platform_util.c)
mcux_add_include(BASE_PATH ${OPENREF_ROOT} INCLUDES
  firmware/system/common firmware/audio_processor/targets/mimxrt595_evk
  firmware/audio_processor/targets/mimxrt595_evk/bootstrap_target)
mcux_add_include(BASE_PATH ${SdkRootDirPath} INCLUDES
  drivers/hashcrypt middleware/mbedtls3x/include middleware/mbedtls3x/library
  ${board_root}/${board}/flash_config)
mcux_add_include(BASE_PATH "${OPENREF_TRUST_DIR}" INCLUDES .)
mcux_add_macro(CC "-DOPENREF_HAS_TRUST_ANCHOR=1")
mcux_add_linker_symbol(SYMBOLS "__stack_size__=0x2000")
mcux_convert_binary(BINARY ${APPLICATION_BINARY_DIR}/${MCUX_SDK_PROJECT_NAME}.bin)
