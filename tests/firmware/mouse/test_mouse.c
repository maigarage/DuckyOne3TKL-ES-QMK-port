#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "quantum.h"
#include "ducky_mouse.h"
static uint8_t mods,layer;
static bool indicator,held[256];
uint8_t get_mods(void) {return mods;}
bool layer_state_is(uint8_t l) {return layer==l;}
void ducky_mouse_set(bool on) {indicator=on;}
void mousekey_on(uint16_t c) {assert(c<256);held[c]=true;}
void mousekey_off(uint16_t c) {assert(c<256);held[c]=false;}
void mousekey_send(void) {}
static bool key(uint16_t code,bool down,unsigned row,unsigned col) {
 keyrecord_t r={0};r.event.key.row=row;r.event.key.col=col;r.event.pressed=down;
 return ducky_mouse_process(code,&r);
}
int main(void) {
 assert(key(KC_SCRL,true,0,15));assert(!indicator);
 assert(key(KC_SCRL,false,0,15));
 layer=1;mods=MOD_MASK_ALT;
 assert(!key(KC_SCRL,true,0,15));assert(indicator);
 mods=0;layer=0;assert(!key(KC_SCRL,false,0,15));
 const uint16_t in[]={KC_HOME,KC_END,KC_DEL,KC_PGDN,KC_INS,KC_PGUP,KC_PSCR,KC_PAUS};
 const uint16_t out[]={MS_UP,MS_DOWN,MS_LEFT,MS_RGHT,MS_BTN1,MS_BTN2,MS_WHLD,MS_WHLU};
 for(unsigned i=0;i<8;i++) {assert(!key(in[i],true,1,i));assert(held[out[i]]);assert(!key(KC_NO,false,1,i));assert(!held[out[i]]);}
 assert(key(KC_A,true,3,1));assert(key(KC_A,false,3,1));
 assert(!key(KC_INS,true,1,14));assert(held[MS_BTN1]);
 assert(!key(QK_KB_10,true,2,15));assert(!indicator);assert(!held[MS_BTN1]);
 assert(!key(QK_KB_10,false,2,15));assert(!key(KC_INS,false,1,14));
 // Normal key-down before enabling must retain normal key-up.
 assert(key(KC_HOME,true,1,15));
 assert(!key(QK_KB_10,true,2,15));assert(!key(QK_KB_10,false,2,15));
 assert(key(KC_HOME,false,1,15));
 // Suspend/release hook must clear every held mouse button/direction.
 assert(!key(KC_INS,true,1,14));assert(!key(KC_HOME,true,1,15));
 ducky_mouse_release();for(unsigned i=0;i<256;i++) assert(!held[i]);
 assert(!key(KC_INS,false,1,14));assert(!key(KC_HOME,false,1,15));
 puts("PASS: chord, indicator, eight mouse mappings, ownership across remaps/mode changes, release on suspend");
}
