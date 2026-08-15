#include "openref_button_filter.h"

#include <stddef.h>
#include <string.h>

bool openref_button_filter_init(openref_button_filter_t *filter,
    const openref_button_filter_config_t *config, uint8_t initial_pressed,
    uint64_t now_ms)
{
    if (filter == NULL || config == NULL || config->debounce_ms == 0u ||
        config->long_press_ms <= config->debounce_ms ||
        (initial_pressed & 0xf0u) != 0u) {
        return false;
    }
    memset(filter, 0, sizeof(*filter));
    filter->config = *config;
    filter->candidate_pressed = initial_pressed;
    filter->stable_pressed = initial_pressed;
    filter->last_tick_ms = now_ms;
    for (uint8_t button = 0u; button < OPENREF_BUTTON_COUNT; button++) {
        filter->candidate_since_ms[button] = now_ms;
        filter->pressed_since_ms[button] = now_ms;
    }
    return true;
}

openref_button_events_t openref_button_filter_update(
    openref_button_filter_t *filter, uint8_t raw_pressed, uint64_t now_ms)
{
    openref_button_events_t events = {0};
    if (filter == NULL || (raw_pressed & 0xf0u) != 0u) {
        return events;
    }
    if (now_ms < filter->last_tick_ms) {
        filter->clock_fault_count++;
        filter->last_tick_ms = now_ms;
        for (uint8_t button = 0u; button < OPENREF_BUTTON_COUNT; button++) {
            filter->candidate_since_ms[button] = now_ms;
        }
        events.stable_pressed = filter->stable_pressed;
        return events;
    }
    filter->last_tick_ms = now_ms;
    for (uint8_t button = 0u; button < OPENREF_BUTTON_COUNT; button++) {
        uint8_t bit = (uint8_t)(1u << button);
        bool raw = (raw_pressed & bit) != 0u;
        bool candidate = (filter->candidate_pressed & bit) != 0u;
        bool stable = (filter->stable_pressed & bit) != 0u;
        if (raw != candidate) {
            filter->candidate_pressed ^= bit;
            filter->candidate_since_ms[button] = now_ms;
            continue;
        }
        if (candidate != stable &&
            now_ms - filter->candidate_since_ms[button] >=
                filter->config.debounce_ms) {
            filter->stable_pressed ^= bit;
            if (candidate) {
                events.pressed |= bit;
                filter->pressed_since_ms[button] = now_ms;
                filter->long_emitted &= (uint8_t)~bit;
            } else {
                events.released |= bit;
                filter->long_emitted &= (uint8_t)~bit;
            }
            stable = candidate;
        }
        if (stable && (filter->long_emitted & bit) == 0u &&
            now_ms - filter->pressed_since_ms[button] >=
                filter->config.long_press_ms) {
            events.long_pressed |= bit;
            filter->long_emitted |= bit;
        }
    }
    events.stable_pressed = filter->stable_pressed;
    return events;
}
