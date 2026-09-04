#include "openref_rt595_boot_coordinator.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t flash[12288];
    uint8_t records[2][OPENREF_CONFIG_SLOT_BYTES];
    uint8_t sum;
    bool fail_reads;
} fake_t;

static bool flash_read(void *context, uint32_t address, uint8_t *data, uint32_t size)
{
    fake_t *fake = context;
    if (fake->fail_reads || address > sizeof(fake->flash) || size > sizeof(fake->flash) - address) return false;
    memcpy(data, &fake->flash[address], size);
    return true;
}
static bool record_read(void *context, uint8_t slot, uint8_t *record)
{
    fake_t *fake = context;
    if (slot > 1u) return false;
    memcpy(record, fake->records[slot], OPENREF_CONFIG_SLOT_BYTES);
    return true;
}
static bool record_write(void *context, uint8_t slot, const uint8_t *record)
{
    fake_t *fake = context;
    if (slot > 1u) return false;
    memcpy(fake->records[slot], record, OPENREF_CONFIG_SLOT_BYTES);
    return true;
}
static bool signature(void *context, const uint8_t *digest, const uint8_t *key, const uint8_t *sig)
{ (void)context; return digest[0] == 0x4fu && key[0] == 0x33u && sig[0] == 0x5au; }
static bool hash_begin(void *context) { ((fake_t *)context)->sum = 0u; return true; }
static bool hash_update(void *context, const uint8_t *data, uint32_t size)
{ fake_t *fake = context; while (size-- != 0u) fake->sum = (uint8_t)(fake->sum + *data++); return true; }
static bool hash_finish(void *context, uint8_t *digest)
{ fake_t *fake = context; for (unsigned i = 0; i < 32u; ++i) digest[i] = (uint8_t)(fake->sum + i); return true; }
static void write32(uint8_t *data, uint32_t value)
{ data[0] = (uint8_t)value; data[1] = (uint8_t)(value >> 8); data[2] = (uint8_t)(value >> 16); data[3] = (uint8_t)(value >> 24); }
static void make_image(fake_t *fake, uint32_t manifest_base, uint32_t image_base, uint32_t version)
{
    uint8_t *manifest = &fake->flash[manifest_base];
    memset(manifest, 0, OPENREF_UPDATE_MANIFEST_BYTES);
    manifest[0] = 0x4f; manifest[1] = 0x52; manifest[2] = 0x55; manifest[3] = 0x50;
    manifest[4] = 1u; manifest[5] = OPENREF_UPDATE_TARGET_AUDIO;
    write32(manifest + 8, 0x1234u); write32(manifest + 12, version);
    write32(manifest + 16, 2u); write32(manifest + 20, 5u);
    for (unsigned i = 0; i < 32u; ++i) manifest[24u + i] = (uint8_t)(15u + i);
    memset(manifest + 56, 0x22, 16); memset(manifest + 72, 0x33, 8); manifest[80] = 0x5a;
    for (unsigned i = 0; i < 5u; ++i) fake->flash[image_base + i] = (uint8_t)(i + 1u);
}

int main(void)
{
    fake_t fake;
    memset(&fake, 0xff, sizeof(fake)); fake.sum = 0u; fake.fail_reads = false;
    make_image(&fake, 0u, 1024u, 6u); make_image(&fake, 4096u, 8192u, 7u);
    openref_update_platform_t platform = {OPENREF_UPDATE_TARGET_AUDIO, 0x1234u, 3u, 5u, 0u, 256u};
    openref_update_crypto_t crypto = {signature, hash_begin, hash_update, hash_finish, &fake};
    openref_rt595_slot_authenticator_t authenticator;
    assert(openref_rt595_slot_authenticator_init(&authenticator,
        (openref_rt595_slot_reader_t){flash_read, &fake}, &platform, crypto,
        0u, 1024u, 256u, 4096u, 8192u, 256u));
    openref_rt595_boot_state_store_t store;
    assert(openref_rt595_boot_state_init(&store,
        (openref_config_backend_t){record_read, record_write, &fake}));
    assert(openref_rt595_boot_state_initialize(&store, OPENREF_BOOT_SLOT_A, 6u));
    openref_boot_slot_t eligible[2] = {{true, true, 6u}, {true, true, 7u}};
    assert(openref_rt595_boot_state_stage(&store, OPENREF_BOOT_SLOT_B, eligible));
    openref_rt595_boot_coordinator_t coordinator;
    assert(openref_rt595_boot_coordinator_init(&coordinator, &authenticator, &store, 2u));
    openref_boot_slot_t authenticated[2];
    openref_boot_decision_t decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_TRIAL && decision.slot == OPENREF_BOOT_SLOT_B);
    assert(authenticated[0].authenticated && authenticated[1].authenticated);
    fake.flash[8192u] ^= 1u;
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_FALLBACK && decision.slot == OPENREF_BOOT_SLOT_A);
    assert(authenticated[0].authenticated && !authenticated[1].authenticated);
    store.loaded = false;
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_NONE && decision.slot == OPENREF_BOOT_NO_SLOT);
    /* With valid durable state but a dead confirmed slot, the authenticated
     * alternate is persisted as a bounded trial, never booted ad hoc. */
    store.loaded = true;
    assert(openref_rt595_boot_state_initialize(&store, OPENREF_BOOT_SLOT_A, 6u) == false);
    fake.flash[8192u] ^= 1u; /* restore B */
    fake.flash[1024u] ^= 1u; /* invalidate confirmed A */
    store.state.pending_slot = OPENREF_BOOT_NO_SLOT;
    store.state.pending_attempts = 0u;
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_TRIAL && decision.slot == OPENREF_BOOT_SLOT_B);
    assert(store.state.pending_slot == OPENREF_BOOT_SLOT_B && store.state.pending_attempts == 1u);
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_TRIAL && store.state.pending_attempts == 2u);
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_NONE);
    assert(store.state.pending_slot == OPENREF_BOOT_SLOT_B && store.state.pending_attempts == 2u);
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_NONE && store.state.pending_attempts == 2u);
    fake.fail_reads = true;
    uint32_t reads = authenticator.read_failures;
    decision = openref_rt595_boot_coordinator_select(&coordinator, authenticated);
    assert(decision.kind == OPENREF_BOOT_DECISION_NONE && authenticator.read_failures > reads);
    puts("openref_rt595_boot_coordinator_test: PASS");
    return 0;
}
