#include "openref_rt595_boot_handoff.h"

#include <limits.h>
#include <stddef.h>
#include <string.h>

static uint32_t load_le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8u) |
           ((uint32_t)p[2] << 16u) | ((uint32_t)p[3] << 24u);
}

static bool valid_region(uint32_t base, uint32_t size) {
    return size != 0u && base <= UINT32_MAX - size;
}

static bool power_of_two(uint32_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}

bool openref_rt595_boot_handoff_prepare(
    openref_rt595_boot_vector_reader_t reader,
    const openref_rt595_boot_handoff_layout_t *layout,
    openref_rt595_boot_handoff_plan_t *plan) {
    uint8_t vectors[OPENREF_RT595_BOOT_VECTOR_BYTES];
    uint32_t image_end;
    uint32_t ram_end;
    uint32_t initial_msp;
    uint32_t reset_handler;
    uint32_t reset_address;

    if (plan != NULL) {
        memset(plan, 0, sizeof(*plan));
    }
    if (layout == NULL || plan == NULL || reader.read == NULL ||
        !layout->authenticated ||
        layout->image_size < OPENREF_RT595_BOOT_VECTOR_BYTES ||
        !valid_region(layout->image_base, layout->image_size) ||
        !valid_region(layout->ram_base, layout->ram_size) ||
        layout->vtor_alignment < OPENREF_RT595_BOOT_MIN_VTOR_ALIGNMENT ||
        !power_of_two(layout->vtor_alignment) ||
        (layout->image_base & (layout->vtor_alignment - 1u)) != 0u) {
        return false;
    }
    if (!reader.read(reader.context, layout->image_base, vectors,
                     sizeof(vectors))) {
        return false;
    }
    image_end = layout->image_base + layout->image_size;
    ram_end = layout->ram_base + layout->ram_size;
    initial_msp = load_le32(vectors);
    reset_handler = load_le32(vectors + 4u);
    reset_address = reset_handler & ~1u;

    /* ARM's full-descending stack may start exactly one byte past RAM, but it
     * must be 8-byte aligned and leave at least one word of usable stack. */
    if ((initial_msp & 7u) != 0u || initial_msp <= layout->ram_base ||
        initial_msp > ram_end || (reset_handler & 1u) == 0u ||
        reset_address < layout->image_base + OPENREF_RT595_BOOT_VECTOR_BYTES ||
        reset_address >= image_end) {
        return false;
    }
    plan->vector_table = layout->image_base;
    plan->initial_msp = initial_msp;
    plan->reset_handler = reset_handler;
    return true;
}

static bool ops_complete(const openref_rt595_boot_handoff_ops_t *ops) {
    return ops != NULL && ops->disable_interrupts != NULL &&
           ops->stop_systick != NULL && ops->clear_interrupt_state != NULL &&
           ops->clean_disable_dcache != NULL && ops->disable_icache != NULL &&
           ops->set_vtor != NULL && ops->synchronize != NULL &&
           ops->set_msp != NULL && ops->branch_to_reset != NULL &&
           ops->fail_closed != NULL;
}

bool openref_rt595_boot_handoff_execute(
    const openref_rt595_boot_handoff_plan_t *plan,
    const openref_rt595_boot_handoff_ops_t *ops) {
    if (!ops_complete(ops)) {
        return false;
    }
    if (plan == NULL || plan->vector_table == 0u || plan->initial_msp == 0u ||
        (plan->reset_handler & 1u) == 0u ||
        !ops->disable_interrupts(ops->context) ||
        !ops->stop_systick(ops->context) ||
        !ops->clear_interrupt_state(ops->context) ||
        !ops->clean_disable_dcache(ops->context) ||
        !ops->disable_icache(ops->context) ||
        !ops->set_vtor(ops->context, plan->vector_table) ||
        !ops->synchronize(ops->context) ||
        !ops->set_msp(ops->context, plan->initial_msp) ||
        !ops->branch_to_reset(ops->context, plan->reset_handler)) {
        (void)ops->fail_closed(ops->context);
        return false;
    }
    /* A branch implementation returning is itself a handoff failure. */
    (void)ops->fail_closed(ops->context);
    return false;
}
