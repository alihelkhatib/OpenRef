#ifndef OPENREF_CREW_SESSION_H
#define OPENREF_CREW_SESSION_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define OPENREF_CREW_MAX_MEMBERS 6u
#define OPENREF_CREW_SESSION_KEY_BYTES 16u

typedef bool (*openref_crew_key_install_fn)(
    void *context,
    uint32_t session_id,
    const uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES]);

typedef bool (*openref_crew_key_erase_fn)(void *context);

typedef struct {
    openref_crew_key_install_fn install;
    openref_crew_key_erase_fn erase;
    void *context;
} openref_crew_key_backend_t;

typedef struct {
    uint32_t session_id;
    uint8_t member_mask;
    uint8_t member_count;
    uint8_t local_node_id;
    bool authenticated;
} openref_crew_admission_t;

typedef struct {
    openref_crew_key_backend_t backend;
    uint32_t active_session_id;
    uint32_t last_session_id;
    uint8_t local_node_id;
    uint8_t member_mask;
    uint32_t activations;
    uint32_t rejected_admissions;
    uint32_t backend_failures;
    bool active;
} openref_crew_session_t;

bool openref_crew_session_init(
    openref_crew_session_t *session,
    uint8_t local_node_id,
    openref_crew_key_backend_t backend);

bool openref_crew_session_activate(
    openref_crew_session_t *session,
    const openref_crew_admission_t *admission,
    uint8_t key[OPENREF_CREW_SESSION_KEY_BYTES]);

bool openref_crew_session_leave(openref_crew_session_t *session);

bool openref_crew_session_contains(
    const openref_crew_session_t *session,
    uint8_t node_id);

#ifdef __cplusplus
}
#endif

#endif
