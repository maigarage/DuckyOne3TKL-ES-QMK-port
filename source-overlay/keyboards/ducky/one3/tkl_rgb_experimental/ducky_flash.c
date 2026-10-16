// SPDX-License-Identifier: GPL-2.0-or-later
/* NUC1261 FMC definitions: OpenNuvoton/NUC1261BSP, fmc.h and NUC1261.h.
 * Fixed APROM settings partition only. No LDROM, CONFIG, SPROM, mass erase,
 * vector remap, voltage or timing register changes are implemented here. */
#include "ducky_store.h"
#include "ducky_safety.h"
#define R(a) (*(volatile uint32_t *)(uintptr_t)(a))
uint32_t ducky_flash_read(uint32_t a) {
    if(a<DUCKY_STORE_BASE || a>=DUCKY_STORE_BASE+2*DUCKY_STORE_BANK_SIZE || (a&3))return 0;
    return R(a);
}
/* Linker copies .ramtext to SRAM. No calls, flash literals or interrupt-driven
 * timeouts while FMC is busy. Watchdog remains active and RGB is already dark. */
__attribute__((section(".ramtext"),noinline,used))
static bool flash_operation(uint32_t a, uint32_t value, bool erase) {
    if(a<DUCKY_STORE_BASE || a>=DUCKY_STORE_BASE+2*DUCKY_STORE_BANK_SIZE ||
       (a&3u) || (erase && a%DUCKY_STORE_PAGE_SIZE))return false;
    if(R(0x50000000)!=0x01205212u || R(0x5000c014)!=0x00033200u)return false;
    if(R(0x5000c010)&1u)return false;
    uint32_t mask, clocks=R(0x50000204), boot=R(0x5000c000)&2u;
    __asm__ volatile("mrs %0, primask\ncpsid i" : "=r"(mask) :: "memory");
    R(0x50000100)=0x59;R(0x50000100)=0x16;R(0x50000100)=0x88;
    R(0x50000204)=clocks|4u;
    R(0x5000c000)=boot|0x49u; /* clear failure; ISPEN/APUEN only */
    R(0x5000c004)=a; R(0x5000c008)=value;
    R(0x5000c00c)=erase?0x22u:0x21u;
    R(0x5000c010)=1;
    __asm__ volatile("dsb\nisb" ::: "memory");
    unsigned limit=1000000u;
    while(R(0x5000c010)&1u) {
        if(--limit==0) { /* cannot safely return into busy flash; WDT resets */
            R(0x50000100)=0;
            for(;;)__asm__ volatile("nop");
        }
    }
    bool ok=!(R(0x5000c000)&0x40u);
    R(0x5000c000)=boot|0x40u; /* clear failure and close ALL update enables */
    R(0x50000204)=clocks;
    R(0x50000100)=0;
    __asm__ volatile("dsb\nisb\nmsr primask, %0" :: "r"(mask) : "memory");
    return ok;
}
bool ducky_flash_program(uint32_t a,uint32_t v) {
    if(!flash_operation(a,v,false) || ducky_flash_read(a)!=v)return false;
    ducky_watchdog_feed();return true; /* only after verified progress */
}
bool ducky_flash_erase(uint32_t a) {
    if(!flash_operation(a,0xffffffffu,true))return false;
    for(unsigned i=0;i<DUCKY_STORE_PAGE_SIZE;i+=4)if(ducky_flash_read(a+i)!=0xffffffffu)return false;
    ducky_watchdog_feed();return true;
}
