#include "ducky_persistence.h"
#include "ducky_mouse.h"
// SPDX-License-Identifier: GPL-2.0-or-later
/* One 3 TKL test10 stock RGB/VIA experiment. See docs/SAFETY.md.
 * Timer scan and protocol recovered from V1.16; hardware validation pending.
 * No LED driver configuration/current commands; explicit settings persistence is separate.
 */
#include "quantum.h"
#include "caps_indicator.h"
#include "ducky_stock.h"
#include "ducky_safety.h"
#include "usb_util.h"
#include <string.h>
#ifdef VIA_ENABLE
#include "via.h"
#endif
#define R32(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define PIN(port, pin) (0x50004200u + (port)*64u + (pin)*4u)
#define SCLK PIN(2,0)
#define LATCH PIN(2,2)
#define SDATA PIN(2,3)
#define PWM_BASE 0x40040000u
static void output(unsigned port, unsigned pin, bool high) {
    uint32_t base=0x50004000u+port*64u;
    uint32_t mfp=0x50000030u+port*8u+(pin/8u)*4u;
    R32(PIN(port,pin))=high; /* Set inactive latch BEFORE selecting output. */
    R32(mfp)&=~(15u<<((pin%8u)*4u));
    R32(base+4u)&=~(1u<<(pin+16u));
    R32(base+12u)&=~(1u<<pin);
    R32(base)=(R32(base)&~(3u<<(pin*2u)))|(1u<<(pin*2u));
}
static void clock_bit(unsigned bit) {
    R32(SDATA)=bit;
    /* Conservative setup/hold relative to the stock 15 MHz transfer. */
    __asm__ volatile("nop\nnop\nnop\nnop" ::: "memory");
    R32(SCLK)=1;
    __asm__ volatile("nop\nnop\nnop\nnop" ::: "memory");
    R32(SCLK)=0;
}
static void shift_bits(uint32_t value, unsigned count) {
    for (unsigned n=count; n; --n) clock_bit((value>>(n-1u))&1u);
}

#define TIMER_BASE 0x40010100u
#define stock_lut ducky_stock_lut
static const uint32_t gates[7]={PIN(2,6),PIN(2,5),PIN(3,7),PIN(3,15),PIN(3,14),PIN(3,13),PIN(5,2)};
static uint16_t pixels[2][7][16][3];
static volatile uint8_t active, pending=255, bank=6, heartbeat;
static volatile bool running, fault;
static volatile uint32_t scan_sequence;
static uint32_t fed_sequence;
static volatile uint8_t max_brightness_percent=90;
static bool initialized, sleeping, caps, scroll, mouse, enabled=true;
static uint8_t brightness=9, mode, channels[3]={10,10,10}, indicator=9;
static bool engine_ready, palette;
static uint16_t zones[2][6][16], draft[6][16], consumed[6];
static bool zone_on[2], paint_caps;
static uint8_t recording, record_hold;
static uint32_t record_started, edit_activity;
static uint8_t paint[3]={10,10,10};
static uint32_t last_render;
static uint32_t mode_pressed;
static bool mode_held;
static void all_rows_off(void) { for(unsigned i=0;i<7;i++) R32(gates[i])=0; }
static uint16_t ceiling(void) { unsigned p=max_brightness_percent; if(p>90)p=90; return 65535u*p/100u; }
static uint16_t capped(uint16_t v,uint16_t c) { return v>c?c:v; }
static uint16_t level(unsigned index) { return stock_lut[index>10?10:index]; }
static void ensure_engine(void) { if(!engine_ready) {ducky_stock_init();ducky_stock_channels(channels);engine_ready=true;} }
static void select_mode(uint8_t value) { ensure_engine();mode=value;ducky_stock_mode(mode);palette=false; }
static bool colored(void) {return mode==0 || mode==6 || mode==7 || mode==8 || mode==9 || mode==10;}
static void send_frame(unsigned row, bool blank) {
    uint16_t cap=ceiling();
    all_rows_off(); /* blank BEFORE shifting, including higher-priority preemption */
    R32(SCLK)=0; R32(LATCH)=0;
    for (unsigned col=0;col<16;col++) {
        /* Independent final clamp also covers queued frames and indicators. */
        const uint16_t *v=pixels[active][row][col];
        uint16_t r=blank?0:capped(v[0],cap), g=blank?0:capped(v[1],cap), b=blank?0:capped(v[2],cap);
        /* Stock red low-bit rule must not round above an even ceiling. */
        if(((r&65534u)|(r>>15))>cap)r-=2;
        shift_bits(((uint32_t)b<<16)|g,32);
        shift_bits(r>>1,15);
        R32(LATCH)=1;
        clock_bit((r>>15)&1u); /* stock 0x385e..0x386c sends bit 15 here, also at full range */
        R32(LATCH)=0;
    }
    clock_bit(0); clock_bit(0); R32(LATCH)=1;
    clock_bit(0); clock_bit(0); clock_bit(0);
    R32(LATCH)=0; R32(SDATA)=0;
}
/* No RTOS services in this IRQ. USB/SysTick have higher priority.
 * Early blanking reduces exposure during transfers; timing needs hardware validation. */
void Vector64(void) {
    all_rows_off();
    R32(TIMER_BASE+8)=1;
    if (!running || fault || !usb_connected_state()) { all_rows_off(); return; }
    if (++heartbeat>50) { all_rows_off(); fault=true; R32(PIN(2,7))=1; return; }
    if(active>1 || (pending!=255 && pending>1) || bank>6) {ducky_safety_cutoff();fault=true;return;}
    bank=(bank+1)%7;
    if (bank==0 && pending!=255) { active=pending; pending=255; }
    send_frame(bank,false);
    /* If shifting crossed a timer period, stop instead of overrunning scan. */
    if (R32(TIMER_BASE+8)&1u) { all_rows_off(); fault=true; R32(PIN(2,7))=1; return; }
    R32(gates[bank])=1;
    scan_sequence++;
}
static void start_timer(void) {
    uint32_t lock=ducky_reg_unlock();
    R32(0x50000208u)|=1u<<3;
    R32(0x50000214u)=(R32(0x50000214u)&~(7u<<12))|(2u<<12);
    R32(TIMER_BASE)=0;
    R32(TIMER_BASE+0x14)=0; R32(TIMER_BASE+0x20)=0;
    R32(TIMER_BASE+4)=(R32(0x50000210u)&(1u<<6))?24000u:48000u;
    R32(TIMER_BASE+8)=1;
    R32(0xe000e280u)=1u<<9;
    /* IRQ9 priority 3; use aligned word access on Cortex-M0 NVIC. */
    R32(0xe000e408u)=(R32(0xe000e408u)&~0xff00u)|0xc000u;
    bank=6; heartbeat=0; running=true;
    R32(0xe000e100u)=1u<<9;
    R32(TIMER_BASE)=(1u<<27)|(1u<<29)|(1u<<30);
    ducky_reg_lock(lock);
}
static void init(void) {
    if(R32(0x50000004)&((1u<<2)|(1u<<8))) {fault=true;ducky_safety_cutoff();return;}
    if(!ducky_watchdog_start()) {fault=true;ducky_safety_cutoff();return;}
    uint32_t lock=ducky_reg_unlock();
    /* PF2 is the stock seventh bank gate (0x3930..0x3948).
     * CONFIG0.CIOINI=1 on the observed device leaves it quasi-bidirectional.
     * Preserve its mode/MFP, as stock does, but control its output latch. */
    R32(PIN(5,2))=0;
    /* Stock 0x394e: PE8 high, PC7 high until data/clock are ready. */
    output(4,8,true); output(2,7,true);
    /* Keep all six gates inactive during initialization.
     * PF2 mode is preserved; its latch participates in all seven scan slots. */
    output(2,6,false); output(2,5,false);
    output(3,7,false); output(3,15,false);
    output(3,14,false); output(3,13,false);
    output(2,0,false); output(2,2,false); output(2,3,false);
    output(5,4,false);
    output(2,1,false);
    send_frame(6, true);
    /* Stock PWM0 CH1 -> PC1, nominal 2 MHz gray clock (same registers at 48 MHz).
     * Select PCLK0 explicitly because test2 uses HIRC48, not PLL. */
    R32(0x50000208u)|=1u<<20;
    R32(0x50000214u)|=1u<<28;
    R32(PWM_BASE+0xd8u)&=~2u;
    R32(PWM_BASE+0x20u)&=~2u;
    R32(PWM_BASE)&=~2u;
    R32(PWM_BASE+4u)&=~((3u<<2)|(1u<<17));
    R32(PWM_BASE+0x14u)=0;
    unsigned period=(R32(0x50000210u)&(1u<<6))?12u:24u;
    R32(PWM_BASE+0x34u)=period-1u;
    R32(PWM_BASE+0x54u)=1u;
    R32(PWM_BASE+0xb0u)=(R32(PWM_BASE+0xb0u)&~(0x30003u<<2))|(2u<<2);
    R32(PWM_BASE+0xb4u)=(R32(PWM_BASE+0xb4u)&~(0x30003u<<2))|(1u<<2);
    R32(PWM_BASE+0xd4u)&=~2u;
    R32(0x50000040u)=(R32(0x50000040u)&~0xf0u)|0x60u;
    R32(PWM_BASE+0xd8u)|=2u;
    R32(PWM_BASE+0x20u)|=2u;
    R32(PIN(2,7))=0;
    initialized=true;
    fed_sequence=scan_sequence;
    ducky_reg_lock(lock);
    start_timer();
}

static void render(uint32_t now) {
    if(active>1) {fault=true;ducky_safety_cutoff();return;}
    if(pending!=255) return;
    unsigned back=active^1u;
    uint16_t limit=level(brightness);
    for(unsigned r=0;r<7;r++) for(unsigned c=0;c<16;c++) {
        uint16_t z=0;
        if(r<6) {
            if(recording) z=draft[r][c];
            else if(zone_on[0] && zones[0][r][c]) z=zones[0][r][c];
            else if(zone_on[1]) z=zones[1][r][c];
        }
        /* Extra spacebar emitters follow a configured spacebar zone. */
        if(r==5 && (c==3 || c==4 || c==6 || c==7)) {
            if(recording && draft[5][5])z=draft[5][5];
            else if(!recording && zone_on[0] && zones[0][5][5])z=zones[0][5][5];
            else if(!recording && zone_on[1] && zones[1][5][5])z=zones[1][5][5];
        }
        for(unsigned k=0;k<3;k++) {
            uint32_t v=0;
            if(r<6) {
                if(palette) v=ducky_stock_palette(r,c,k);
                else if(recording && r==3 && c==0) v=level(paint[k]);
                else if(z) v=level((z>>(k*4))&15);
                else if(!recording && enabled) v=ducky_stock_pixel(r,c,k);
                v=v*limit/65535u;
            } else if((c==5 && caps) || (c==6 && scroll) || (c==7 && mouse)) v=level(indicator);
            pixels[back][r][c][k]=(uint16_t)v;
        }
    }
    __asm__ volatile("" ::: "memory");
    pending=back;
}
void ducky_caps_set(bool on) { caps=on; last_render=0; }
void ducky_scroll_set(bool on) { scroll=on; last_render=0; }
void ducky_mouse_set(bool on) { mouse=on; last_render=0; }
void ducky_rgb_suspend(void) {
    if(sleeping)return;
    sleeping=true; running=false;
    if(engine_ready)ducky_stock_release();
    recording=record_hold=0;palette=paint_caps=mode_held=false;memset(consumed,0,sizeof consumed);
    if(!initialized) return;
    R32(0xe000e180u)=1u<<9;
    R32(TIMER_BASE)=0;
    all_rows_off(); R32(PIN(2,7))=1;
    send_frame(6,true);
    /* Cut rows/PC7 before disabling the autonomous gray clock. */
    R32(PWM_BASE+0xd8u)&=~2u;R32(PWM_BASE+0x20u)&=~2u;
    ducky_watchdog_stop();
}
void ducky_rgb_resume(void) {
    sleeping=false;
    /* Reinitialize only from foreground after USB is configured again. */
    initialized=false;
}
void ducky_caps_task(void) {
    uint32_t now=timer_read32();
    if(!usb_connected_state()) {ducky_rgb_suspend();return;}
    if(sleeping)ducky_rgb_resume();
    if(fault || now<1500) return;
    if(recording>2 || record_hold>2 || mode>=12) {fault=true;ducky_safety_cutoff();return;}
    if(running && scan_sequence!=fed_sequence) {
        fed_sequence=scan_sequence;ducky_watchdog_feed();
    }
    heartbeat=0;
    ensure_engine();
    if(mode_held && now-mode_pressed>=3000) {
        enabled=false;zone_on[0]=zone_on[1]=false;palette=false;recording=0;
        mode_held=false;last_render=0;
    }
    if(record_hold && now-record_started>=5000) {
        recording=record_hold;record_hold=0;memcpy(draft,zones[recording-1],sizeof draft);
        edit_activity=now;palette=false;paint_caps=false;
    }
    if(recording && now-edit_activity>=30000) {recording=0;palette=false;paint_caps=false;}
    if(!initialized) { render(now); init(); }
    /* Follow completed bank scans, not an independent 16 ms oscillator.
     * pending is cleared only at bank 0. Stock dispatch periods are 1/7/4/8/10/2 frames. */
    if(pending==255) {ducky_stock_step();render(now);last_render=now;}
}
static void choose_palette(unsigned r,unsigned c) {
    uint8_t *v=recording?paint:channels;
    for(unsigned k=0;k<3;k++) {
        uint16_t raw=ducky_stock_palette(r,c,k);unsigned i=0;
        while(i<10 && stock_lut[i+1]<=raw)i++;
        v[k]=i;
    }
    if(!recording)ducky_stock_channels(channels);
    palette=false;
}
bool ducky_rgb_process(uint16_t keycode,keyrecord_t *record) {
    if(recording>2 || record_hold>2) {fault=true;ducky_safety_cutoff();return true;}
    bool pressed=record->event.pressed;
    unsigned r=record->event.key.row,c=record->event.key.col;
    ensure_engine();
    if(r<6 && c<16) {
        ducky_stock_key(r,c,pressed);
        if(!pressed && (consumed[r]&(1u<<c))) {
            consumed[r]&=~(1u<<c);
            if(r==3 && c==0)paint_caps=false;
            return false;
        }
    }
    if(recording && keycode==KC_CAPS) {
        paint_caps=pressed;if(pressed && r<6 && c<16)consumed[r]|=1u<<c;return false;
    }
    if(pressed && r<6 && c<16 && (palette || recording) && keycode!=MO(1)) {
        edit_activity=timer_read32();consumed[r]|=1u<<c;
        if(recording && paint_caps) {
            if(keycode>=KC_F5 && keycode<=KC_F7)paint[keycode-KC_F5]=(paint[keycode-KC_F5]+1)%11;
            else if(keycode==KC_F8)memset(paint,0,sizeof paint);
            else if(keycode==KC_SPC)palette=!palette;
            else if(keycode==KC_SCRL) {memcpy(zones[recording-1],draft,sizeof draft);zone_on[recording-1]=true;recording=0;palette=false;paint_caps=false;}
        } else if(palette) choose_palette(r,c);
        else draft[r][c]=draft[r][c]?0:0x8000|paint[0]|(paint[1]<<4)|(paint[2]<<8);
        return false;
    }
    if(keycode==QK_KB_5) {
        if(pressed) {mode_pressed=timer_read32();mode_held=true;}
        else if(mode_held) {select_mode((mode+1)%12);enabled=true;mode_held=false;}
        return false;
    }
    if(keycode==QK_KB_14 || keycode==QK_KB_15) {
        if(pressed) {record_hold=keycode-QK_KB_14+1;record_started=timer_read32();}
        else record_hold=0;
        return false;
    }
    if(keycode<QK_KB_0 || keycode>QK_KB_15 || keycode==QK_KB_10)return true;
    if(!pressed)return false;
    switch(keycode-QK_KB_0) {
        case 0:case 1:case 2:
            if(colored()) {unsigned k=keycode-QK_KB_0;channels[k]=(channels[k]+1)%11;ducky_stock_channels(channels);}break;
        case 3: if(colored()) {memset(channels,0,sizeof channels);ducky_stock_channels(channels);}break;
        case 4: enabled=!enabled;break;
        case 6: if(get_mods()&MOD_MASK_ALT) {if(indicator<10)indicator++;}else if(brightness<10)brightness++;break;
        case 7: if(get_mods()&MOD_MASK_ALT) {if(indicator>1)indicator--;}else if(brightness>0)brightness--;break;
        case 8: ducky_stock_speed(ducky_stock_get_speed()+1);break;
        case 9: {uint8_t v=ducky_stock_get_speed();if(v)ducky_stock_speed(v-1);break;}
        case 11: if(colored())palette=!palette;break;
        case 12:case 13: zone_on[keycode-QK_KB_12]=!zone_on[keycode-QK_KB_12];break;
    }
    return false;
}
#ifdef VIA_ENABLE
/* VIA v3 RGB controls; persistence tracks changes in the foreground. */
void via_custom_value_command_kb(uint8_t *data,uint8_t length) {
    if(length<3)return;
    if(data[1]==2){ducky_settings_command(data,length);return;}
    if(data[1]==1 && data[0]==id_custom_get_value && length>=8) {
        static const uint32_t regs[]={0x50000004,0x50000018,0x50000024,0x40004000,0x50000210,0x50000214,0x50000218};
        if(data[2]>7) {data[0]=id_unhandled;return;}
        uint32_t v=data[2]==7?((uint32_t)fault|((uint32_t)running<<1)|((uint32_t)max_brightness_percent<<8)):R32(regs[data[2]]);
        memcpy(data+4,&v,4);return;
    }
    if(data[1]!=0) {data[0]=id_unhandled;return;}
    if(data[0]==id_custom_save) return; /* RAM only; no implicit flash write */
    if(length<4 || (data[0]!=id_custom_set_value && data[0]!=id_custom_get_value)) {data[0]=id_unhandled;return;}
    uint8_t id=data[2],v=data[3];ensure_engine();
    if(id<1 || id>12) {data[0]=id_unhandled;return;}
    if(data[0]==id_custom_set_value) {
        switch(id) {
            case 12:max_brightness_percent=v>90?90:v;break;
            case 1:enabled=!!v;break;
            case 2:if(v<12)select_mode(v);break;
            case 3:brightness=v>10?10:v;break;
            case 4:ducky_stock_speed(v);break;
            case 5:case 6:case 7:channels[id-5]=v>10?10:v;ducky_stock_channels(channels);break;
            case 8:indicator=v<1?1:v>10?10:v;break;
            case 9:palette=!!v;break;
            case 10:case 11:zone_on[id-10]=!!v;break;
        }
    } else {
        switch(id) {
            case 12:v=max_brightness_percent;break;
            case 1:v=enabled;break;case 2:v=mode;break;case 3:v=brightness;break;
            case 4:v=ducky_stock_get_speed();break;
            case 5:case 6:case 7:v=channels[id-5];break;case 8:v=indicator;break;
            case 9:v=palette;break;case 10:case 11:v=zone_on[id-10];break;
        }
        data[3]=v;
    }
}
#endif

/* Versioned RGB settings only: no RNG, animation buffers or pressed-key state. */
void ducky_rgb_export(uint8_t *d) {
    ensure_engine();memset(d,0,416);
    d[0]=1;d[1]=enabled;d[2]=mode;d[3]=brightness;
    memcpy(d+4,channels,3);d[7]=indicator;d[8]=max_brightness_percent;
    d[9]=zone_on[0]|(zone_on[1]<<1);d[10]=ducky_mouse_enabled();
    ducky_stock_export_speeds(d+12);memcpy(d+32,zones,sizeof zones);
}
bool ducky_rgb_import(const uint8_t *d) {
    if(d[0]!=1 || d[1]>1 || d[2]>=12 || d[3]>10 || d[4]>10 || d[5]>10 || d[6]>10 ||
       d[7]<1 || d[7]>10 || d[8]>90 || d[9]>3 || d[10]>1)return false;
    for(unsigned i=0;i<12;i++)if(d[12+i]>(i==9?10:9))return false;
    for(unsigned i=32;i<416;i+=2) {
        unsigned v=d[i]|((unsigned)d[i+1]<<8);
        if((v&0x7000u) || (v&15)>10 || ((v>>4)&15)>10 || ((v>>8)&15)>10)return false;
    }
    ensure_engine();enabled=d[1];brightness=d[3];memcpy(channels,d+4,3);
    indicator=d[7];max_brightness_percent=d[8];zone_on[0]=d[9]&1;zone_on[1]=!!(d[9]&2);
    memcpy(zones,d+32,sizeof zones);ducky_stock_import_speeds(d+12);
    select_mode(d[2]);ducky_stock_channels(channels);ducky_mouse_restore(d[10]);last_render=0;
    return true;
}
void ducky_rgb_defaults(void) {
    enabled=true;brightness=9;mode=0;channels[0]=channels[1]=channels[2]=10;
    indicator=9;max_brightness_percent=90;zone_on[0]=zone_on[1]=false;
    memset(zones,0,sizeof zones);memset(draft,0,sizeof draft);memset(consumed,0,sizeof consumed);
    paint[0]=paint[1]=paint[2]=10;recording=record_hold=0;
    palette=paint_caps=mode_held=false;ducky_stock_init();engine_ready=true;
    ducky_stock_channels(channels);ducky_mouse_restore(false);last_render=0;
}

bool ducky_rgb_editing(void) { return recording || record_hold; }
