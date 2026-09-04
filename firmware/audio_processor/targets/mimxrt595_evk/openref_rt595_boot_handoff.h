#ifndef OPENREF_RT595_BOOT_HANDOFF_H
#define OPENREF_RT595_BOOT_HANDOFF_H

#include <stdbool.h>
#include <stdint.h>

#define OPENREF_RT595_BOOT_VECTOR_BYTES 8u
#define OPENREF_RT595_BOOT_MIN_VTOR_ALIGNMENT 128u

typedef bool (*openref_rt595_boot_vector_read_fn)(void *context,
                                                  uint32_t address,
                                                  uint8_t *destination,
                                                  uint32_t length);

typedef struct {
    openref_rt595_boot_vector_read_fn read;
    void *context;
} openref_rt595_boot_vector_reader_t;

typedef struct {
    bool authenticated;
    uint32_t image_base;
    uint32_t image_size;
    uint32_t ram_base;
    uint32_t ram_size;
    uint32_t vtor_alignment;
} openref_rt595_boot_handoff_layout_t;

typedef struct {
    uint32_t vector_table;
    uint32_t initial_msp;
    uint32_t reset_handler;
} openref_rt595_boot_handoff_plan_t;

typedef bool (*openref_rt595_boot_step_fn)(void *context);
typedef bool (*openref_rt595_boot_set_word_fn)(void *context, uint32_t value);

typedef struct {
    openref_rt595_boot_step_fn disable_interrupts;
    openref_rt595_boot_step_fn stop_systick;
    openref_rt595_boot_step_fn clear_interrupt_state;
    openref_rt595_boot_step_fn clean_disable_dcache;
    openref_rt595_boot_step_fn disable_icache;
    openref_rt595_boot_set_word_fn set_vtor;
    openref_rt595_boot_step_fn synchronize;
    openref_rt595_boot_set_word_fn set_msp;
    openref_rt595_boot_set_word_fn branch_to_reset;
    openref_rt595_boot_step_fn fail_closed;
    void *context;
} openref_rt595_boot_handoff_ops_t;

bool openref_rt595_boot_handoff_prepare(
    openref_rt595_boot_vector_reader_t reader,
    const openref_rt595_boot_handoff_layout_t *layout,
    openref_rt595_boot_handoff_plan_t *plan);

/* A successful reset-handler branch must not return.  Consequently this
 * function always returns false; return means the fail-closed hook ran. */
bool openref_rt595_boot_handoff_execute(
    const openref_rt595_boot_handoff_plan_t *plan,
    const openref_rt595_boot_handoff_ops_t *ops);

#endif
