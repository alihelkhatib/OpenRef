#ifndef OPENREF_SECURITY_COUNTERS_FG23_H
#define OPENREF_SECURITY_COUNTERS_FG23_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    OPENREF_COUNTER_ADMISSION = 1,
    OPENREF_COUNTER_SERVICE = 2
} openref_security_counter_domain_t;

typedef struct {
    openref_security_counter_domain_t domain;
} openref_security_counter_context_t;

bool openref_security_counter_fg23_load(
    openref_security_counter_domain_t domain,
    uint32_t *persisted_counter);

bool openref_security_counter_fg23_persist(
    void *context,
    uint32_t next_counter);

#endif
