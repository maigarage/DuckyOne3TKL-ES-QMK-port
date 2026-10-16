// SPDX-License-Identifier: GPL-2.0-or-later
#include "hal.h"
#define REG32(a) (*(volatile uint32_t *)(a))
uint32_t SystemCoreClock = 48000000;
uint32_t CyclesPerUs = 48;
uint32_t PllClock = 0;
extern void ducky_safety_halt(void);
static void wait_stable(uint32_t bit) {
    for(unsigned n=0;n<1000000;n++) if(REG32(0x5000020c)&bit)return;
    REG32(0x50000100)=0;ducky_safety_halt();
}
void NUC123_clock_init(void) {
    /* NUC1261: protected register unlock, HIRC and HIRC48 stabilization. */
    REG32(0x50000100)=0x59; REG32(0x50000100)=0x16; REG32(0x50000100)=0x88;
    REG32(0x50000200) |= 4;
    wait_stable(0x10);
    REG32(0x50000210) = (REG32(0x50000210)&~7u)|7u;
    REG32(0x50000218) &= ~15u;
    REG32(0x50000200) |= 1u<<13;
    wait_stable(0x20);
    REG32(0x50000210) = (REG32(0x50000210)&~7u)|4u;
    /* USBDSEL=0 chooses HIRC48 directly, not the NUC123 PLL divider. */
    REG32(0x50000234) &= ~(1u<<8);
    REG32(0x50000100)=0;
    SystemCoreClock=48000000; CyclesPerUs=48;
}
void hal_lld_init(void) {}
