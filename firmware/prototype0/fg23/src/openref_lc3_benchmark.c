#include "openref_lc3_benchmark.h"

#ifdef OPENREF_APP_LC3_BENCHMARK

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "app_common.h"
#include "lc3.h"

#define OPENREF_LC3_FRAME_US 10000
#define OPENREF_LC3_SAMPLE_RATE_HZ 16000
#define OPENREF_LC3_SAMPLES_PER_FRAME 160
#define OPENREF_LC3_BYTES_PER_FRAME 40
#define OPENREF_LC3_REMOTE_SOURCES 5
#define OPENREF_LC3_REPORT_INTERVAL_US 1000000u

static lc3_encoder_mem_16k_t encoder_memory;
static lc3_decoder_mem_16k_t decoder_memory[OPENREF_LC3_REMOTE_SOURCES];
static lc3_encoder_t encoder;
static lc3_decoder_t decoders[OPENREF_LC3_REMOTE_SOURCES];
static int16_t input_pcm[OPENREF_LC3_SAMPLES_PER_FRAME];
static int16_t output_pcm[OPENREF_LC3_REMOTE_SOURCES][OPENREF_LC3_SAMPLES_PER_FRAME];
static uint8_t encoded[OPENREF_LC3_BYTES_PER_FRAME];
static uint32_t next_report_us;
static uint32_t runs;
static uint32_t failures;
static bool ready;

void openref_lc3_benchmark_init(void)
{
    encoder = lc3_setup_encoder(
        OPENREF_LC3_FRAME_US,
        OPENREF_LC3_SAMPLE_RATE_HZ,
        OPENREF_LC3_SAMPLE_RATE_HZ,
        &encoder_memory);
    ready = encoder != NULL;
    for (uint8_t index = 0u; index < OPENREF_LC3_REMOTE_SOURCES; index++) {
        decoders[index] = lc3_setup_decoder(
            OPENREF_LC3_FRAME_US,
            OPENREF_LC3_SAMPLE_RATE_HZ,
            OPENREF_LC3_SAMPLE_RATE_HZ,
            &decoder_memory[index]);
        ready = ready && decoders[index] != NULL;
    }
    for (uint16_t index = 0u; index < OPENREF_LC3_SAMPLES_PER_FRAME; index++) {
        input_pcm[index] = (int16_t)(((int32_t)(index % 40u) - 20) * 512);
    }
    next_report_us = RAIL_GetTime() + OPENREF_LC3_REPORT_INTERVAL_US;
    printf("\r\n{{(openrefLc3)}{Status:%s}{EncoderState:%u}{DecoderState:%u}{Decoders:%u}{PcmBytes:%u}{BitstreamBytes:%u}}}\r\n",
           ready ? "Ready" : "SetupFail",
           (unsigned int)sizeof(encoder_memory),
           (unsigned int)sizeof(decoder_memory[0]),
           (unsigned int)OPENREF_LC3_REMOTE_SOURCES,
           (unsigned int)(sizeof(input_pcm) + sizeof(output_pcm)),
           (unsigned int)sizeof(encoded));
}

void openref_lc3_benchmark_process(void)
{
    if (!ready) {
        return;
    }
    uint32_t now_us = RAIL_GetTime();
    if ((int32_t)(now_us - next_report_us) < 0) {
        return;
    }

    uint32_t encode_start_us = RAIL_GetTime();
    int encode_result = lc3_encode(
        encoder,
        LC3_PCM_FORMAT_S16,
        input_pcm,
        1,
        sizeof(encoded),
        encoded);
    uint32_t encode_done_us = RAIL_GetTime();

    int decode_result = 0;
    for (uint8_t index = 0u; index < OPENREF_LC3_REMOTE_SOURCES; index++) {
        decode_result |= lc3_decode(
            decoders[index],
            encoded,
            sizeof(encoded),
            LC3_PCM_FORMAT_S16,
            output_pcm[index],
            1);
    }
    uint32_t decode_done_us = RAIL_GetTime();
    if (encode_result != 0 || decode_result != 0) {
        failures++;
    }
    runs++;
    printf("\r\n{{(openrefLc3)}{Status:Run}{Runs:%lu}{EncodeUs:%lu}{FiveDecodeUs:%lu}{TotalUs:%lu}{Failures:%lu}}}\r\n",
           (unsigned long)runs,
           (unsigned long)(encode_done_us - encode_start_us),
           (unsigned long)(decode_done_us - encode_done_us),
           (unsigned long)(decode_done_us - encode_start_us),
           (unsigned long)failures);
    next_report_us = now_us + OPENREF_LC3_REPORT_INTERVAL_US;
}

#else

void openref_lc3_benchmark_init(void) {}
void openref_lc3_benchmark_process(void) {}

#endif
