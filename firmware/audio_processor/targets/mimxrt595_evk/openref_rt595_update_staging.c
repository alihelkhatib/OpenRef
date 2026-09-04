#include "openref_rt595_update_staging.h"
#include <limits.h>
#include <stddef.h>
#include <string.h>
static void fail(openref_rt595_update_staging_t *s)
{
    if (s->failures != UINT32_MAX) {
        ++s->failures;
    }
    if (s->verifier != NULL) {
        s->verifier->active = false;
        s->verifier->verified = false;
    }
    s->active = false;
}
static bool flush(openref_rt595_update_staging_t *s)
{
    uint8_t verify[OPENREF_RT595_UPDATE_MAX_PAGE_BYTES];
    if(s->buffered==0u)return true;
    uint16_t image_bytes = s->buffered;
    memset(&s->page[s->buffered],0xff,s->page_bytes-s->buffered);
    if(!s->flash.program(s->flash.context,s->base+s->offset,s->page,s->page_bytes)||
       !s->flash.read(s->flash.context,s->base+s->offset,verify,s->page_bytes)||
       memcmp(s->page,verify,s->page_bytes)!=0){fail(s);return false;}
    /* Authenticate the bytes read back from the staging slot, not the caller's
       transient input buffer. Padding is verified as erased but not hashed. */
    if (!openref_update_verifier_write(s->verifier, verify, image_bytes)) {
        fail(s);
        return false;
    }
    s->offset+=s->page_bytes;s->buffered=0u;return true;
}
bool openref_rt595_update_staging_init(openref_rt595_update_staging_t *s, openref_rt595_update_flash_t f,
 uint32_t manifest_base,uint32_t base,uint32_t capacity,uint32_t sector,uint32_t page)
{
    if(!s||!f.read||!f.erase||!f.program||!capacity||!sector||!page||page>sizeof(s->page)||
       sector%page||manifest_base%sector||base%sector||capacity%sector||
       manifest_base>UINT32_MAX-sector||manifest_base+sector!=base||base>UINT32_MAX-capacity)return false;
    memset(s,0,sizeof(*s));s->flash=f;s->manifest_base=manifest_base;s->base=base;s->capacity=capacity;s->sector_bytes=sector;s->page_bytes=page;return true;
}
bool openref_rt595_update_staging_start(openref_rt595_update_staging_t *s,openref_update_verifier_t *v)
{
    uint32_t erase_bytes;
    if(!s||s->active||!v||!v->active||v->verified||v->manifest.image_size==0u||v->manifest.image_size>s->capacity||
       v->manifest.image_size>UINT32_MAX-(s->sector_bytes-1u))return false;
    erase_bytes=((v->manifest.image_size+s->sector_bytes-1u)/s->sector_bytes)*s->sector_bytes;
    s->verifier=v;
    /* Erase the inactive manifest first. It remains invalid until the image is
       completely authenticated and is committed last. */
    if(!s->flash.erase(s->flash.context,s->manifest_base,s->sector_bytes)||
       !s->flash.erase(s->flash.context,s->base,erase_bytes)){fail(s);return false;}
    s->offset=0;s->buffered=0;s->active=true;memset(s->page,0xff,s->page_bytes);return true;
}
bool openref_rt595_update_staging_write(openref_rt595_update_staging_t *s,const uint8_t *data,uint32_t length)
{
    if(!s||!s->active||!data||length==0u||
       s->offset>s->verifier->manifest.image_size||
       s->buffered>s->verifier->manifest.image_size-s->offset||
       length>s->verifier->manifest.image_size-s->offset-s->buffered)return false;
    while(length){uint32_t room=s->page_bytes-s->buffered,n=length<room?length:room;memcpy(&s->page[s->buffered],data,n);s->buffered+=(uint16_t)n;data+=n;length-=n;if(s->buffered==s->page_bytes&&!flush(s))return false;}return true;
}
bool openref_rt595_update_staging_finish(openref_rt595_update_staging_t *s)
{
    if(!s||!s->active)return false;
    /* No verified state is published until the final padded page is committed,
       read back, and included in the digest. */
    if (!flush(s)) {
        return false;
    }
    if (!openref_update_verifier_finish(s->verifier)) {
        fail(s);
        return false;
    }
    /* The signed manifest is the commit record. Publish it only after the
       complete image is durable and verified, then read it back exactly. */
    s->verifier->verified = false;
    memset(s->page, 0xff, s->page_bytes);
    memcpy(s->page, s->verifier->manifest_wire, OPENREF_UPDATE_MANIFEST_BYTES);
    uint8_t verify[OPENREF_RT595_UPDATE_MAX_PAGE_BYTES];
    if (!s->flash.program(s->flash.context, s->manifest_base, s->page, s->page_bytes) ||
        !s->flash.read(s->flash.context, s->manifest_base, verify, s->page_bytes) ||
        memcmp(s->page, verify, s->page_bytes) != 0) {
        fail(s);
        return false;
    }
    s->verifier->verified = true;
    s->active = false;
    return true;
}
void openref_rt595_update_staging_abort(openref_rt595_update_staging_t *s){if(s){if(s->verifier){s->verifier->active=false;s->verifier->verified=false;}s->active=false;s->buffered=0;s->verifier=NULL;memset(s->page,0,sizeof(s->page));}}
