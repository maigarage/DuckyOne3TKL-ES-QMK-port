// SPDX-License-Identifier: GPL-2.0-or-later
/* Two independently erasable banks. Commit marker is programmed LAST.
 * Only an erased partition or one containing our valid snapshot is writable.
 * Unknown contents fail closed; a failed operation never erases the old bank. */
#include "ducky_store.h"
#define HEADER 32u
#define SEAL 0x54494d43u
static uint32_t crc_byte(uint32_t crc, uint8_t value) {
    crc ^= value;
    for (unsigned i=0;i<8;i++) crc=(crc>>1)^((0u-(crc&1u))&0xedb88320u);
    return crc;
}
static uint32_t crc_word(uint32_t crc, uint32_t value) {
    for(unsigned i=0;i<4;i++) {crc=crc_byte(crc,(uint8_t)value);value>>=8;}
    return crc;
}
static uint32_t base(unsigned bank) {return DUCKY_STORE_BASE+bank*DUCKY_STORE_BANK_SIZE;}
static uint32_t checksum(unsigned bank, bool source) {
    uint32_t crc=0xffffffffu;
    /* Header fields including sequence are covered, except CRC and seal. */
    for(unsigned i=0;i<20;i+=4) crc=crc_word(crc,ducky_flash_read(base(bank)+i));
    for(unsigned i=0;i<DUCKY_STORE_PAYLOAD;i+=4)
        crc=crc_word(crc,source?ducky_store_source_word(i):ducky_flash_read(base(bank)+HEADER+i));
    return ~crc;
}
static bool valid(unsigned bank) {
    uint32_t a=base(bank);
    return ducky_flash_read(a)==DUCKY_STORE_MAGIC &&
           ducky_flash_read(a+4)==DUCKY_STORE_SCHEMA &&
           ducky_flash_read(a+8)==DUCKY_STORE_PAYLOAD &&
           ducky_flash_read(a+16)==~ducky_flash_read(a+12) &&
           ducky_flash_read(a+24)==0xffffffffu && ducky_flash_read(a+28)==SEAL &&
           ducky_flash_read(a+20)==checksum(bank,false);
}
int ducky_store_latest(void) {
    bool a=valid(0),b=valid(1);
    if(!a)return b?1:-1;
    if(!b)return 0;
    uint32_t delta=ducky_flash_read(base(1)+12)-ducky_flash_read(base(0)+12);
    return delta && delta<0x80000000u?1:0;
}
int ducky_store_load(void) {
    int bank=ducky_store_latest();
    if(bank<0)return bank;
    for(unsigned i=0;i<DUCKY_STORE_PAYLOAD;i+=4)
        ducky_store_restore_word(i,ducky_flash_read(base((unsigned)bank)+HEADER+i));
    return bank;
}
static bool blank(void) {
    for(unsigned i=0;i<2*DUCKY_STORE_BANK_SIZE;i+=4)
        if(ducky_flash_read(DUCKY_STORE_BASE+i)!=0xffffffffu)return false;
    return true;
}
int ducky_store_save(void) {
    int old=ducky_store_latest();
    if(old<0 && !blank())return -2;
    if(old>=0) {
        bool same=true;
        for(unsigned i=0;i<DUCKY_STORE_PAYLOAD;i+=4)
            if(ducky_store_source_word(i)!=ducky_flash_read(base((unsigned)old)+HEADER+i)){same=false;break;}
        if(same)return 2;
    }
    unsigned bank=old==0?1:0;
    uint32_t a=base(bank), seq=old<0?1:ducky_flash_read(base((unsigned)old)+12)+1;
    for(unsigned i=0;i<DUCKY_STORE_BANK_SIZE;i+=DUCKY_STORE_PAGE_SIZE)
        if(!ducky_flash_erase(a+i))return -1;
    uint32_t fields[5]={DUCKY_STORE_MAGIC,DUCKY_STORE_SCHEMA,DUCKY_STORE_PAYLOAD,seq,~seq};
    for(unsigned i=0;i<5;i++)if(!ducky_flash_program(a+i*4,fields[i]))return -1;
    for(unsigned i=0;i<DUCKY_STORE_PAYLOAD;i+=4)
        if(!ducky_flash_program(a+HEADER+i,ducky_store_source_word(i)))return -1;
    uint32_t crc=checksum(bank,true);
    if(!ducky_flash_program(a+20,crc) || checksum(bank,false)!=crc)return -1;
    if(!ducky_flash_program(a+28,SEAL) || !valid(bank))return -1;
    return 1;
}
