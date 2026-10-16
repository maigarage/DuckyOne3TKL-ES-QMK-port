// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#include "caps_indicator.h"
#include "ducky_mouse.h"
#include "ducky_safety.h"
#include "ducky_persistence.h"
#define R32(a) (*(volatile uint32_t *)(uintptr_t)(a))
static uint32_t factory_trim;
void keyboard_pre_init_kb(void) {
    factory_trim=R32(0x50000118);
    keyboard_pre_init_user();
}
void keyboard_post_init_kb(void) {ducky_settings_init();keyboard_post_init_user();}
void housekeeping_task_kb(void) {
    uint32_t lock=ducky_reg_unlock();
    if(R32(0x50000088)&0x600u) {
        R32(0x50000118)=factory_trim;
        R32(0x50000090)=0;
        R32(0x50000088)=0x600u;
        R32(0x40060004)=0x10u;
    } else if((R32(0x50000090)&3u)!=2u && (R32(0x40060004)&0x10u)) {
        R32(0x40060004)=0x10u;
        R32(0x50000090)=0x512u;
    }
    ducky_reg_lock(lock);
    ducky_settings_task();
    ducky_caps_task();
    housekeeping_task_user();
}
/* No flash writes. LDROM entry depends on the stock bootloader's policy.
 * This is an experimental request, NOT a guaranteed recovery mechanism. */
void bootloader_jump(void) {
    ducky_safety_cutoff();
    ducky_rgb_suspend();
    __disable_irq();
    R32(0x50000100)=0x59; R32(0x50000100)=0x16; R32(0x50000100)=0x88;
    R32(0x5000c000)=(R32(0x5000c000)&~1u)|2u;
    __DSB();
    R32(0xe000ed0c)=0x05fa0004;
    while(1){}
}

bool led_update_kb(led_t state) {
    bool result=led_update_user(state);
    if (result) { ducky_caps_set(state.caps_lock); ducky_scroll_set(state.scroll_lock); }
    return result;
}

void suspend_power_down_kb(void) { ducky_mouse_release(); ducky_rgb_suspend(); suspend_power_down_user(); }
void suspend_wakeup_init_kb(void) { ducky_rgb_resume(); suspend_wakeup_init_user(); }
bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    if(!ducky_rgb_process(keycode,record)) return false;
    if(!ducky_mouse_process(keycode,record)) return false;
    return process_record_user(keycode,record);
}
