// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#include "eeprom_driver.h"
#include "via.h"
#include "usb_util.h"
#include "ducky_store.h"
#include "ducky_persistence.h"
#include "ducky_safety.h"
#include "caps_indicator.h"
#include "ducky_mouse.h"
#include <string.h>
#define R(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define SAMPLE_MS 250u
/* Keep legacy snapshot layout. Always store auto-save OFF; legacy ON is ignored.
 * No automatic-write scheduler exists in this revision. */
#define AUTO_OFFSET 24u
static uint8_t eeprom_cache[DUCKY_EEPROM_SIZE] __attribute__((aligned(4)));
static uint8_t rgb_cache[DUCKY_RGB_SIZE] __attribute__((aligned(4)));
static bool loaded, initialized, tracking, dirty;
static uint8_t request, status;
static uint32_t sampled_at;
static bool target_ok(void) {
    return R(0x50000000)==0x01205212u && R(0x5000c014)==0x00033200u;
}
static void changed(void) {
    if(tracking)dirty=true;
}
static void export_settings(uint8_t *data) {
    ducky_rgb_export(data);data[AUTO_OFFSET]=0xa0;
}
uint32_t ducky_store_source_word(uint32_t i) {
    uint32_t v=0;
    if(i<DUCKY_EEPROM_SIZE)memcpy(&v,eeprom_cache+i,4);
    else if(i<DUCKY_STORE_PAYLOAD)memcpy(&v,rgb_cache+i-DUCKY_EEPROM_SIZE,4);
    return v;
}
void ducky_store_restore_word(uint32_t i,uint32_t v) {
    if(i<DUCKY_EEPROM_SIZE)memcpy(eeprom_cache+i,&v,4);
    else if(i<DUCKY_STORE_PAYLOAD)memcpy(rgb_cache+i-DUCKY_EEPROM_SIZE,&v,4);
}
void eeprom_driver_init(void) {
    if(initialized)return;
    initialized=true;
    if(!target_ok()){status=7;return;}
    loaded=ducky_store_load()>=0;
    /* A build-date change must not discard a same-schema keymap. */
    if(loaded){via_eeprom_set_valid(true);status=1;}
}
void eeprom_driver_erase(void){memset(eeprom_cache,0,sizeof eeprom_cache);changed();}
void eeprom_driver_format(bool erase){if(erase)eeprom_driver_erase();}
static size_t clamp(const void *addr,size_t n) {
    uintptr_t a=(uintptr_t)addr;
    if(a>=DUCKY_EEPROM_SIZE)return 0;
    return n>DUCKY_EEPROM_SIZE-a?DUCKY_EEPROM_SIZE-a:n;
}
void eeprom_read_block(void *dst,const void *addr,size_t n) {
    memset(dst,0,n);n=clamp(addr,n);if(n)memcpy(dst,eeprom_cache+(uintptr_t)addr,n);
}
void eeprom_write_block(const void *src,void *addr,size_t n) {
    n=clamp(addr,n);
    if(n && memcmp(eeprom_cache+(uintptr_t)addr,src,n)) {
        memcpy(eeprom_cache+(uintptr_t)addr,src,n);changed();
    }
}
void ducky_settings_init(void) {
    if(loaded) {
        if(!ducky_rgb_import(rgb_cache) || (rgb_cache[AUTO_OFFSET]!=0 &&
           rgb_cache[AUTO_OFFSET]!=0xa0 && rgb_cache[AUTO_OFFSET]!=0xa1)) {
            ducky_rgb_defaults();status=5;
        }
    }
    export_settings(rgb_cache);
    sampled_at=timer_read32();
    dirty=false;tracking=true;
}
static void text_reply(uint8_t *d,uint8_t n,const char *s) {
    memset(d+3,0,n-3);strncpy((char *)d+3,s,n-4);
}
/* Keep a symbol for linked-firmware protocol regression and debugging. */
__attribute__((noinline,used))
void ducky_settings_command(uint8_t *d,uint8_t n) {
    if(n<4){if(n)d[0]=id_unhandled;return;}
    uint8_t id=d[2];
    if(d[0]==id_custom_get_value) {
        if(id==0) {
            d[3]=status;
            if(n>=8){d[4]=10;d[5]=3;d[6]=loaded;d[7]=0;}
            if(n>=12){d[8]=0;d[9]=dirty;d[10]=0;d[11]=request;}
        } else if(id<=3)d[3]=0;
        else if(id==4) {
            static const char *const labels[]={"Defaults (not saved)","Loaded from flash","Waiting for keys/CM editor","Saved and verified","Already saved","Write failed; old copy kept","Unknown flash: not erased","Target mismatch: blocked","Legacy reset status","Defaults in RAM: click Save"};
            text_reply(d,n,labels[status<10?status:5]);
        } else if(id==5)d[3]=0; /* Legacy GUI cannot enable automatic writes. */
        else if(id==6)text_reply(d,n,"Restore changes RAM only");
        else if(id==7)text_reply(d,n,request?"Operation queued":dirty?"RAM changed: click Save":"No pending changes");
        else d[0]=id_unhandled;
        return;
    }
    if(d[0]==id_custom_save)return; /* VIA sends this after UI changes; not a flash trigger. */
    if(d[0]!=id_custom_set_value || id<1 || (id>3 && id!=5) || d[3]>1) {
        d[0]=id_unhandled;return;
    }
    /* Recognized but currently disallowed actions still get a valid protocol ACK.
     * Firmware status is the operation result; ACK does NOT mean reset/saved. */
    if(request)return;
    /* IDs 2 (old Arm) and 5 (old auto-save toggle) are harmless legacy no-ops.
     * Only explicit ID 1 can queue a flash transaction. ID 3 resets RAM only. */
    if(d[3]==1 && (id==1 || id==3)){request=id==1?1:2;status=2;}

}
void ducky_settings_task(void) {
    if(!tracking)return;
    if(timer_elapsed32(sampled_at)>=SAMPLE_MS) {
        uint8_t current[DUCKY_RGB_SIZE];export_settings(current);
        if(memcmp(current,rgb_cache,sizeof current)) {
            memcpy(rgb_cache,current,sizeof current);changed();
        }
        sampled_at=timer_read32();
    }
    if(!request)return; /* Hard gate: idle time/edits/imports can NEVER write flash. */
    if(!usb_connected_state() || ducky_rgb_editing())return;
    for(unsigned r=0;r<MATRIX_ROWS;r++)if(matrix_get_row(r))return;
    unsigned action=request;request=0;
    if(action==1 && !target_ok()){status=7;return;}
    ducky_mouse_release();ducky_rgb_suspend();
    if(action==2) {
        clear_keyboard();eeconfig_init();eeconfig_read_keymap(&keymap_config);
        layer_clear();default_layer_set(1);
        ducky_rgb_defaults();
        export_settings(rgb_cache);dirty=true;status=9;
        ducky_rgb_resume();return; /* Restore defaults does not persist anything. */
    }
    export_settings(rgb_cache);
    if(!ducky_watchdog_start()){status=5;ducky_safety_halt();}
    int result=ducky_store_save();
    status=result==1?3:result==2?4:result==-2?6:5;
    if(result>0){loaded=true;dirty=false;}
    else dirty=true; /* Only another explicit Save may retry. */
    ducky_watchdog_stop();
    ducky_rgb_resume();
}
