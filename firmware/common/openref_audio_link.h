#ifndef OPENREF_AUDIO_LINK_H
#define OPENREF_AUDIO_LINK_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_AUDIO_LINK_MAGIC 0x414fu
#define OPENREF_AUDIO_LINK_VERSION 1u
#define OPENREF_AUDIO_LINK_HEADER_BYTES 16u
#define OPENREF_AUDIO_LINK_PAYLOAD_BYTES 80u
#define OPENREF_AUDIO_LINK_CRC_BYTES 2u
#define OPENREF_AUDIO_LINK_FRAME_BYTES 98u
#define OPENREF_AUDIO_LINK_QUEUE_CAPACITY 4u

#define OPENREF_AUDIO_LINK_FLAG_FRAME_0_VALID 0x01u
#define OPENREF_AUDIO_LINK_FLAG_FRAME_1_VALID 0x02u
#define OPENREF_AUDIO_LINK_FLAG_DISCONTINUITY 0x04u

typedef enum {
    OPENREF_AUDIO_LINK_LOCAL_AUDIO = 1,
    OPENREF_AUDIO_LINK_REMOTE_AUDIO = 2,
    OPENREF_AUDIO_LINK_STATUS = 3
} openref_audio_link_kind_t;

typedef struct {
    uint8_t kind;
    uint8_t source_id;
    uint8_t flags;
    uint16_t sequence;
    uint32_t timestamp_us;
    uint8_t producer_queue_depth;
    uint8_t payload[OPENREF_AUDIO_LINK_PAYLOAD_BYTES];
} openref_audio_link_frame_t;

typedef struct {
    openref_audio_link_frame_t entries[OPENREF_AUDIO_LINK_QUEUE_CAPACITY];
    uint8_t head;
    uint8_t count;
    uint32_t pushes;
    uint32_t pops;
    uint32_t overruns;
} openref_audio_link_queue_t;

uint16_t openref_audio_link_crc16(const uint8_t *data, uint16_t length);

bool openref_audio_link_encode(
    const openref_audio_link_frame_t *frame,
    uint8_t *wire,
    uint16_t capacity);

bool openref_audio_link_decode(
    const uint8_t *wire,
    uint16_t length,
    openref_audio_link_frame_t *frame);

void openref_audio_link_queue_init(openref_audio_link_queue_t *queue);

bool openref_audio_link_queue_push(
    openref_audio_link_queue_t *queue,
    const openref_audio_link_frame_t *frame);

bool openref_audio_link_queue_pop(
    openref_audio_link_queue_t *queue,
    openref_audio_link_frame_t *frame);

#ifdef __cplusplus
}
#endif

#endif
