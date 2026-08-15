#include <assert.h>

#include "openref_button_filter.h"

static openref_button_filter_t make_filter(void)
{
    openref_button_filter_config_t config = {20u, 500u};
    openref_button_filter_t filter;
    assert(openref_button_filter_init(&filter, &config, 0u, 100u));
    return filter;
}

static void test_bounce_generates_one_press_and_release(void)
{
    openref_button_filter_t filter = make_filter();
    assert(openref_button_filter_update(&filter, 1u, 110u).pressed == 0u);
    assert(openref_button_filter_update(&filter, 0u, 115u).pressed == 0u);
    assert(openref_button_filter_update(&filter, 1u, 120u).pressed == 0u);
    openref_button_events_t events =
        openref_button_filter_update(&filter, 1u, 140u);
    assert(events.pressed == 1u && events.stable_pressed == 1u);
    assert(openref_button_filter_update(&filter, 0u, 150u).released == 0u);
    events = openref_button_filter_update(&filter, 0u, 170u);
    assert(events.released == 1u && events.stable_pressed == 0u);
}

static void test_long_press_is_one_shot_and_per_button(void)
{
    openref_button_filter_t filter = make_filter();
    openref_button_filter_update(&filter, 0x05u, 110u);
    openref_button_events_t events =
        openref_button_filter_update(&filter, 0x05u, 130u);
    assert(events.pressed == 0x05u);
    events = openref_button_filter_update(&filter, 0x05u, 630u);
    assert(events.long_pressed == 0x05u);
    events = openref_button_filter_update(&filter, 0x05u, 900u);
    assert(events.long_pressed == 0u);
}

static void test_clock_rollback_emits_no_action(void)
{
    openref_button_filter_t filter = make_filter();
    openref_button_filter_update(&filter, 1u, 120u);
    openref_button_events_t events =
        openref_button_filter_update(&filter, 1u, 119u);
    assert(events.pressed == 0u && events.long_pressed == 0u);
    assert(filter.clock_fault_count == 1u);
}

int main(void)
{
    test_bounce_generates_one_press_and_release();
    test_long_press_is_one_shot_and_per_button();
    test_clock_rollback_emits_no_action();
    return 0;
}
