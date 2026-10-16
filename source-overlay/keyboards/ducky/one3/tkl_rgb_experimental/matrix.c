// SPDX-License-Identifier: GPL-2.0-or-later
#include "quantum.h"
#define R32(a) (*(volatile uint32_t *)(uintptr_t)(a))
typedef struct { uint8_t port, pin; } ducky_pin_t;
static const ducky_pin_t rows[6]={{3,0},{3,8},{3,9},{3,1},{3,2},{3,3}};
static const ducky_pin_t cols[16]={{0,3},{0,2},{0,1},{0,0},{1,0},{1,1},{1,2},{1,3},{1,4},{1,8},{1,11},{4,2},{1,15},{1,5},{1,6},{1,7}};
static void output(ducky_pin_t p, bool high) { R32(0x50004200u+p.port*64u+p.pin*4u)=high; }
static void configure(ducky_pin_t p, bool out) {
    unsigned base=0x50004000u+p.port*64u;
    unsigned mfp=0x50000030u+p.port*8u+(p.pin/8u)*4u;
    unsigned shift=(p.pin%8u)*4u;
    R32(mfp)&=~(15u<<shift);
    R32(base+4)&=~(1u<<(p.pin+16));
    R32(base+12)&=~(1u<<p.pin);
    output(p,true);
    R32(base)=(R32(base)&~(3u<<(p.pin*2)))|((out?1u:0u)<<(p.pin*2));
}
void matrix_init_custom(void) {
    for(unsigned i=0;i<16;i++) configure(cols[i],false);
    for(unsigned i=0;i<6;i++) configure(rows[i],true);
}
bool matrix_scan_custom(matrix_row_t current_matrix[]) {
    bool changed=false;
    for(unsigned r=0;r<6;r++) {
        output(rows[r],false); wait_us(5);
        matrix_row_t value=0;
        for(unsigned c=0;c<16;c++) {
            ducky_pin_t p=cols[c];
            if(!(R32(0x50004010u+p.port*64u)&(1u<<p.pin))) value|=(matrix_row_t)1u<<c;
        }
        output(rows[r],true);
        if(current_matrix[r]!=value){current_matrix[r]=value;changed=true;}
    }
    return changed;
}
