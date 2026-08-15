#ifndef OPENREF_BUTTON_FILTER_H
#define OPENREF_BUTTON_FILTER_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_BUTTON_COUNT 4u

typedef struct {
    uint32_t debounce_ms;
    uint32_t long_press_ms;
} openref_button_filter_config_t;

typedef struct {
    uint8_t pressed;
    uint8_t released;
    uint8_t long_pressed;
    uint8_t stable_pressed;
} openref_button_events_t;

typedef struct {
    openref_button_filter_config_t config;
    uint64_t last_tick_ms;
    uint64_t candidate_since_ms[OPENREF_BUTTON_COUNT];
    uint64_t pressed_since_ms[OPENREF_BUTTON_COUNT];
    uint8_t candidate_pressed;
    uint8_t stable_pressed;
    uint8_t long_emitted;
    uint32_t clock_fault_count;
} openref_button_filter_t;

bool openref_button_filter_init(
    openref_button_filter_t *filter,
    const openref_button_filter_config_t *config,
    uint8_t initial_pressed,
    uint64_t now_ms);

openref_button_events_t openref_button_filter_update(
    openref_button_filter_t *filter,
    uint8_t raw_pressed,
    uint64_t now_ms);

#endif
