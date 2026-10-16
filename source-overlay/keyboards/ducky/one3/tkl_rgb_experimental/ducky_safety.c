// SPDX-License-Identifier: GPL-2.0-or-later
/* NUC1261 register definitions checked against OpenNuvoton NUC1261BSP.
 * No CONFIG/FMC/LDROM writes, voltage threshold or LED current gain changes. */
#include "ducky_safety.h"
#define R(a) (*(volatile uint32_t *)(uintptr_t)(a))
uint32_t ducky_reg_unlock(void) {
    uint32_t mask;
    __asm__ volatile("mrs %0, primask\ncpsid i" : "=r"(mask) :: "memory");
    R(0x50000100)=0x59; R(0x50000100)=0x16; R(0x50000100)=0x88;
    return mask;
}
void ducky_reg_lock(uint32_t state) {
    R(0x50000100)=0;
    __asm__ volatile("msr primask, %0" :: "r"(state) : "memory");
}
static bool synchronized(void) {
    for (unsigned n=0;n<200000;n++) if(!(R(0x40004000)&(1u<<30))) return true;
    return false;
}
void ducky_watchdog_stop(void) {
    uint32_t m=ducky_reg_unlock();
    R(0xe000e180)=2; /* WDT IRQ1 */
    R(0x50000200)|=8;
    unsigned n;
    for(n=0;n<200000;n++)if(R(0x5000020c)&8)break;
    if(n==200000) {ducky_reg_lock(m);ducky_safety_halt();}
    R(0x50000214)=(R(0x50000214)&~3u)|3u;
    R(0x50000208)|=1; /* WDT peripheral clock */
    R(0x40004000)=0; /* no CONFIG bits changed */
    ducky_reg_lock(m);
    if(!synchronized() || (R(0x40004000)&0x80u)) ducky_safety_halt();
    R(0xe000e280)=2;
}
bool ducky_watchdog_start(void) {
    uint32_t m=ducky_reg_unlock();
    R(0x50000200)|=8; /* independent nominal 10 kHz LIRC */
    unsigned n;
    for(n=0;n<200000;n++) if(R(0x5000020c)&8) break;
    if(n==200000) {ducky_reg_lock(m);return false;}
    R(0x50000208)|=1;
    R(0x50000214)=(R(0x50000214)&~3u)|3u;
    R(0x40004004)=2; /* reset 18 LIRC ticks after timeout */
    R(0xe000e400)&=~0xff00u; /* WDT IRQ1 priority 0 */
    R(0xe000e280)=2;
    R(0xe000e100)=2;
    R(0x40004008)=0x5aa5;
    /* 1024 LIRC ticks, reset + interrupt; don't pause while debugger stops CPU. */
    R(0x40004000)=0x800003c2u;
    ducky_reg_lock(m);
    return synchronized() && (R(0x40004000)&0x382u)==0x382u;
}
void ducky_watchdog_feed(void) { R(0x40004008)=0x5aa5; }
void ducky_safety_early(void) {
    uint32_t m=ducky_reg_unlock();
    /* Inactive latches before changing mode/MFP. PF2 mode intentionally retained. */
    ducky_safety_cutoff();
    const uint8_t ports[7]={2,2,2,3,3,3,3}, pins[7]={7,6,5,7,15,14,13};
    for(unsigned i=0;i<7;i++) {
        unsigned port=ports[i],pin=pins[i],base=0x50004000u+port*64u;
        R(0x50000030u+port*8u+(pin/8u)*4u)&=~(15u<<((pin%8u)*4u));
        R(base+4u)&=~(1u<<(pin+16u));R(base+12u)&=~(1u<<pin);
        R(base)=(R(base)&~(3u<<(pin*2u)))|(1u<<(pin*2u));
    }
    ducky_reg_lock(m);
    ducky_watchdog_stop();
}
