#include "openref_security.h"

#include <stddef.h>

static void write_u32_le(uint8_t *buffer, uint32_t value)
{
    for (uint8_t index = 0u; index < 4u; index++) {
        buffer[index] = (uint8_t)(value >> (index * 8u));
    }
}

static uint32_t read_u32_le(const uint8_t *buffer)
{
    uint32_t value = 0u;
    for (uint8_t index = 0u; index < 4u; index++) {
        value |= (uint32_t)buffer[index] << (index * 8u);
    }
    return value;
}

static bool counter_after(uint32_t candidate, uint32_t reference)
{
    return (int32_t)(candidate - reference) > 0;
}

void openref_security_build_nonce(
    uint32_t crew_session_id,
    uint8_t source_id,
    uint32_t boot_counter,
    uint32_t packet_counter,
    uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES])
{
    if (nonce == NULL) {
        return;
    }
    write_u32_le(&nonce[0], crew_session_id);
    nonce[4] = source_id;
    write_u32_le(&nonce[5], boot_counter);
    write_u32_le(&nonce[9], packet_counter);
}

openref_security_replay_result_t openref_security_accept_authenticated(
    openref_security_replay_state_t *state,
    uint32_t boot_counter,
    uint32_t packet_counter)
{
    if (state == NULL) {
        return OPENREF_SECURITY_REPLAY_REJECT_STALE;
    }
    if (!state->initialized) {
        state->boot_counter = boot_counter;
        state->highest_packet_counter = packet_counter;
        state->received_bitmap = 1u;
        state->initialized = true;
        return OPENREF_SECURITY_REPLAY_ACCEPT_FIRST;
    }
    if (boot_counter != state->boot_counter) {
        if (!counter_after(boot_counter, state->boot_counter)) {
            return OPENREF_SECURITY_REPLAY_REJECT_OLD_BOOT;
        }
        state->boot_counter = boot_counter;
        state->highest_packet_counter = packet_counter;
        state->received_bitmap = 1u;
        return OPENREF_SECURITY_REPLAY_ACCEPT_NEW;
    }
    if (counter_after(packet_counter, state->highest_packet_counter)) {
        uint32_t shift = packet_counter - state->highest_packet_counter;
        state->received_bitmap = shift >= OPENREF_SECURITY_REPLAY_WINDOW_BITS
            ? 1u
            : (state->received_bitmap << shift) | 1u;
        state->highest_packet_counter = packet_counter;
        return OPENREF_SECURITY_REPLAY_ACCEPT_NEW;
    }
    uint32_t age = state->highest_packet_counter - packet_counter;
    if (age >= OPENREF_SECURITY_REPLAY_WINDOW_BITS) {
        return OPENREF_SECURITY_REPLAY_REJECT_STALE;
    }
    uint64_t bit = UINT64_C(1) << age;
    if ((state->received_bitmap & bit) != 0u) {
        return OPENREF_SECURITY_REPLAY_REJECT_DUPLICATE;
    }
    state->received_bitmap |= bit;
    return OPENREF_SECURITY_REPLAY_ACCEPT_REORDERED;
}

bool openref_security_protect(
    openref_security_ccm_encrypt_fn encrypt,
    void *context,
    uint32_t crew_session_id,
    uint8_t source_id,
    uint32_t boot_counter,
    uint32_t packet_counter,
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    uint8_t envelope[OPENREF_SECURITY_ENVELOPE_BYTES])
{
    if (encrypt == NULL || aad == NULL || plaintext == NULL || envelope == NULL ||
        source_id == 0u || source_id == UINT8_MAX) {
        return false;
    }
    uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES];
    openref_security_build_nonce(
        crew_session_id, source_id, boot_counter, packet_counter, nonce);
    write_u32_le(&envelope[0], boot_counter);
    write_u32_le(&envelope[4], packet_counter);
    return encrypt(
        context, nonce, aad, plaintext, &envelope[OPENREF_SECURITY_PREFIX_BYTES],
        &envelope[OPENREF_SECURITY_PREFIX_BYTES +
                  OPENREF_SECURITY_PLAINTEXT_BYTES]);
}

bool openref_security_open(
    openref_security_ccm_decrypt_fn decrypt,
    void *context,
    uint32_t crew_session_id,
    uint8_t source_id,
    const uint8_t aad[OPENREF_SECURITY_AAD_BYTES],
    const uint8_t envelope[OPENREF_SECURITY_ENVELOPE_BYTES],
    openref_security_replay_state_t *replay,
    uint8_t plaintext[OPENREF_SECURITY_PLAINTEXT_BYTES],
    openref_security_replay_result_t *replay_result)
{
    if (decrypt == NULL || aad == NULL || envelope == NULL || replay == NULL ||
        plaintext == NULL || replay_result == NULL || source_id == 0u ||
        source_id == UINT8_MAX) {
        return false;
    }
    uint32_t boot_counter = read_u32_le(&envelope[0]);
    uint32_t packet_counter = read_u32_le(&envelope[4]);
    uint8_t nonce[OPENREF_SECURITY_NONCE_BYTES];
    openref_security_build_nonce(
        crew_session_id, source_id, boot_counter, packet_counter, nonce);
    if (!decrypt(
            context, nonce, aad, &envelope[OPENREF_SECURITY_PREFIX_BYTES],
            &envelope[OPENREF_SECURITY_PREFIX_BYTES +
                      OPENREF_SECURITY_PLAINTEXT_BYTES], plaintext)) {
        return false;
    }
    *replay_result = openref_security_accept_authenticated(
        replay, boot_counter, packet_counter);
    return *replay_result <= OPENREF_SECURITY_REPLAY_ACCEPT_REORDERED;
}
