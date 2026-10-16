// SPDX-License-Identifier: GPL-2.0-or-later
/* Adapter only. Vendor calculations are isolated in ducky_stock_blob.S. */
#include "ducky_stock.h"
#include <string.h>
uint8_t ducky_stock_ram[0x1724] __attribute__((aligned(4)));
uint8_t ducky_stock_rng[0x8c] __attribute__((aligned(4)));
extern const uint8_t ducky_stock_blob[];
static const uint8_t initial[0x1724]={
#include "ducky_stock_initial.inc"
};
const uint16_t ducky_stock_lut[11]={0,1024,2048,4096,6656,9216,12288,16384,28672,36864,65535};
static const uint16_t inits[12]={0x266,0x26e,0x46c,0x866,0x9e2,0x66e,0xc00,0xdbc,0x110e,0x10a8,0x136c,0x1f4a};
static const uint16_t updates[12]={0x266,0x2f8,0x4f0,0x880,0xa18,0x68c,0xc98,0xe4c,0x11ac,0x10a8,0x13fc,0x1ff8};
static const uint8_t periods[12]={1,7,4,4,4,4,8,8,4,10,2,4};
static const uint8_t order[12]={9,1,2,3,4,5,6,7,8,10,11,0};
static const uint8_t speed_offsets[12]={0,0x39,0x3a,0x3b,0x3c,0x38,0x35,0x36,0x34,0,0x37,0x3d};
static uint8_t current, ticks;
static void valid_current(void) {if(current>=12)current=0;}
static void call(uint16_t offset) { ((void (*)(void))((uintptr_t)ducky_stock_blob+offset+1))(); }
void ducky_stock_init(void) { memcpy(ducky_stock_ram,initial,sizeof initial);memset(ducky_stock_rng,0,sizeof ducky_stock_rng);ducky_stock_mode(0); }
void ducky_stock_mode(uint8_t mode) { if(mode>=12)return;current=order[mode];ducky_stock_ram[1]=current;ticks=0;call(inits[current]); }
void ducky_stock_step(void) {valid_current(); if(++ticks>=periods[current]) {ticks=0;call(updates[current]);} }
/* V1.16 RAM 0x200002f4: five electrical slots use another geometric position.
 * Same inverse mapping as stock 0x4eee and renderer 0x3ebe. */
static void geometry(uint8_t *r,uint8_t *c) {
    static const uint8_t route[5][4]={{0,1,0,16},{3,14,1,16},{3,15,2,16},{4,14,4,15},{4,15,5,16}};
    for(unsigned i=0;i<5;i++)if(*r==route[i][0] && *c==route[i][1]) {*r=route[i][2];*c=route[i][3];return;}
}
void ducky_stock_key(uint8_t row,uint8_t col,bool pressed) { if(row<6 && col<16) {geometry(&row,&col);ducky_stock_ram[0x29f4-0x1754+row*17+col]=pressed?0:2;} }
void ducky_stock_channels(const uint8_t v[3]) {valid_current(); for(unsigned k=0;k<3;k++)ducky_stock_ram[0x2c+k]=v[k]>10?10:v[k];call(0x2534);call(inits[current]);ticks=0; }
uint8_t ducky_stock_get_speed(void) {valid_current(); uint8_t p=speed_offsets[current];if(!p)return 0;uint8_t v=ducky_stock_ram[p];return current==10?11-v:current==11?v-3:v; }
void ducky_stock_speed(uint8_t v) {valid_current();uint8_t p=speed_offsets[current];if(!p)return;uint8_t max=current==10?10:9;if(v>max)v=max;ducky_stock_ram[p]=current==10?11-v:current==11?v+3:v;call(0x2534);call(inits[current]);ticks=0;}
static uint16_t pixel(unsigned base,uint8_t row,uint8_t col,uint8_t ch) {if(row>=6||col>=16||ch>=3)return 0;geometry(&row,&col);unsigned i=base+row*102+col*6+ch*2;return ducky_stock_ram[i]|((uint16_t)ducky_stock_ram[i+1]<<8);}
uint16_t ducky_stock_pixel(uint8_t r,uint8_t c,uint8_t k) {return pixel(0x40,r,c,k);}
uint16_t ducky_stock_palette(uint8_t r,uint8_t c,uint8_t k) {return pixel(0x1fd8-0x1754,r,c,k);}

void ducky_stock_release(void) {memset(ducky_stock_ram+0x29f4-0x1754,2,102);}

void ducky_stock_export_speeds(uint8_t values[12]) {
    for(unsigned i=0;i<12;i++) {
        unsigned k=order[i],p=speed_offsets[k];
        uint8_t v=p?ducky_stock_ram[p]:0;
        if(p)v=k==10?11-v:k==11?v-3:v;
        values[i]=v>(k==10?10:9)?(k==10?10:9):v;
    }
}
void ducky_stock_import_speeds(const uint8_t values[12]) {
    for(unsigned i=0;i<12;i++) {
        unsigned k=order[i],p=speed_offsets[k];uint8_t v=values[i];
        if(v>(k==10?10:9))v=k==10?10:9;
        if(p)ducky_stock_ram[p]=k==10?11-v:k==11?v+3:v;
    }
}
