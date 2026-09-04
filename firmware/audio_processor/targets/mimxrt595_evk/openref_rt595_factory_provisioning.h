#ifndef OPENREF_RT595_FACTORY_PROVISIONING_H
#define OPENREF_RT595_FACTORY_PROVISIONING_H
#include <stdbool.h>
#include <stdint.h>
typedef enum { OPENREF_RT595_FACTORY_CONFIG=0, OPENREF_RT595_FACTORY_BOOT_STATE=1, OPENREF_RT595_FACTORY_IDENTITY=2, OPENREF_RT595_FACTORY_REGION_COUNT=3 } openref_rt595_factory_region_t;
typedef enum { OPENREF_RT595_FACTORY_PROBE_IO=0, OPENREF_RT595_FACTORY_PROBE_BLANK, OPENREF_RT595_FACTORY_PROBE_MATCH, OPENREF_RT595_FACTORY_PROBE_OTHER_VALID, OPENREF_RT595_FACTORY_PROBE_CORRUPT } openref_rt595_factory_probe_t;
typedef enum { OPENREF_RT595_FACTORY_FAILED=0, OPENREF_RT595_FACTORY_PROVISIONED, OPENREF_RT595_FACTORY_ALREADY_PROVISIONED, OPENREF_RT595_FACTORY_UNAUTHORIZED, OPENREF_RT595_FACTORY_LOCKED_MISMATCH, OPENREF_RT595_FACTORY_NONBLANK, OPENREF_RT595_FACTORY_WRITE_FAILED, OPENREF_RT595_FACTORY_VERIFY_FAILED, OPENREF_RT595_FACTORY_LOCK_FAILED } openref_rt595_factory_result_t;
typedef struct { const uint8_t *bytes; uint32_t length; } openref_rt595_factory_blob_t;
typedef struct {
 bool (*manufacturing_authorized)(void *); bool (*lock_is_set)(void *,bool *);
 openref_rt595_factory_probe_t (*probe)(void *,openref_rt595_factory_region_t,const uint8_t *,uint32_t);
 bool (*program_blank)(void *,openref_rt595_factory_region_t,const uint8_t *,uint32_t);
 bool (*readback_equal)(void *,openref_rt595_factory_region_t,const uint8_t *,uint32_t);
 bool (*set_lock_once)(void *); void *context;
} openref_rt595_factory_driver_t;
typedef struct { openref_rt595_factory_blob_t region[OPENREF_RT595_FACTORY_REGION_COUNT]; } openref_rt595_factory_plan_t;
openref_rt595_factory_result_t openref_rt595_factory_provision(const openref_rt595_factory_driver_t *,const openref_rt595_factory_plan_t *);
#endif
