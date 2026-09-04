#ifndef OPENREF_RT595_AUDIO_IO_MCUX_H
#define OPENREF_RT595_AUDIO_IO_MCUX_H
#include "fsl_dmic_dma.h"
#include "fsl_i2s_dma.h"
#include "openref_rt595_audio_io.h"
typedef struct {DMIC_Type*dmic;I2S_Type*i2s;DMA_Type*dma;uint32_t dmic_channel,dmic_dma_channel,i2s_dma_channel;} openref_rt595_audio_io_mcux_config_t;
typedef struct {openref_rt595_audio_io_t io;openref_rt595_audio_io_mcux_config_t config;dma_handle_t dmic_dma,i2s_dma;dmic_dma_handle_t dmic_handle;i2s_dma_handle_t i2s_handle;int16_t stereo[OPENREF_RT595_AUDIO_IO_BLOCK_SAMPLES*2u];uint32_t critical_primask;} openref_rt595_audio_io_mcux_t;
/* Board code configures DMIC, I2S, codec, pins, clocks and calls DMA_Init once. */
bool openref_rt595_audio_io_mcux_init(openref_rt595_audio_io_mcux_t*,const openref_rt595_audio_io_mcux_config_t*);
#endif
