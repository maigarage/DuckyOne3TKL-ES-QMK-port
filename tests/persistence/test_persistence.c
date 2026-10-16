// SPDX-License-Identifier: GPL-2.0-or-later
/* POSIX host integration: production persistence controller + dual-bank store.
 * Fixed MMIO target IDs are mapped; no USB or physical flash is accessed. */
#define _GNU_SOURCE
#include "quantum.h"
#include "eeprom_driver.h"
#include "ducky_persistence.h"
#include "ducky_store.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
uint32_t now,keymap_config;
uint16_t keys;
bool connected=true;
static bool editing, suspended, fail_write;
static uint8_t rgb[DUCKY_RGB_SIZE],flash[8192];
static unsigned erases, programs, resets;
void ducky_rgb_export(uint8_t *p){memcpy(p,rgb,sizeof rgb);}
bool ducky_rgb_import(const uint8_t *p){memcpy(rgb,p,sizeof rgb);return true;}
void ducky_rgb_defaults(void){memset(rgb,0,sizeof rgb);rgb[0]=1;rgb[3]=9;rgb[4]=rgb[5]=rgb[6]=10;rgb[7]=9;rgb[8]=90;}
bool ducky_rgb_editing(void){return editing;}
void ducky_mouse_release(void){}
void ducky_rgb_suspend(void){suspended=true;}
void ducky_rgb_resume(void){suspended=false;}
bool ducky_watchdog_start(void){return true;}
void ducky_watchdog_stop(void){}
void ducky_safety_halt(void){abort();}
void clear_keyboard(void){}
void layer_clear(void){}
void default_layer_set(uint32_t l){assert(l==1);}
void eeconfig_read_keymap(void *p){memset(p,0,4);}
void via_eeprom_set_valid(bool valid){assert(valid);}
void eeconfig_init(void){uint8_t defaults[2048]={0};eeprom_write_block(defaults,0,sizeof defaults);resets++;}
uint32_t ducky_flash_read(uint32_t a){assert(a>=DUCKY_STORE_BASE && a<0x20000);uint32_t v;memcpy(&v,flash+a-DUCKY_STORE_BASE,4);return v;}
bool ducky_flash_erase(uint32_t a){assert(suspended && a>=DUCKY_STORE_BASE && a+2048<=0x20000);erases++;if(fail_write)return false;memset(flash+a-DUCKY_STORE_BASE,255,2048);return true;}
bool ducky_flash_program(uint32_t a,uint32_t v){assert(suspended && a>=DUCKY_STORE_BASE && a+4<=0x20000);programs++;if(fail_write)return false;memcpy(flash+a-DUCKY_STORE_BASE,&v,4);return true;}
static uint8_t reply[32];
static void cmd(unsigned id,unsigned v){memset(reply,0,32);reply[0]=7;reply[1]=2;reply[2]=id;reply[3]=v;ducky_settings_command(reply,32);assert(reply[0]==7);}
static uint8_t state(void){memset(reply,0,32);reply[0]=8;reply[1]=2;ducky_settings_command(reply,32);assert(reply[0]==8 && reply[4]==10 && reply[5]==3);return reply[3];}
static void tick(uint32_t t){now=t;ducky_settings_task();}
static void edit(uint8_t v){eeprom_write_block(&v,(void *)100,1);}
static void save(void){cmd(1,1);ducky_settings_task();assert(state()==3||state()==4);}
int main(int argc,char **argv){
 assert(argc==2);int test=atoi(argv[1]);
 assert(mmap((void *)0x50000000,0x10000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void *)-1);
 *(uint32_t *)0x50000000=0x01205212;*(uint32_t *)0x5000c014=0x33200;
 memset(flash,255,sizeof flash);ducky_rgb_defaults();
 eeprom_driver_init();ducky_settings_init();
 switch(test){
 case 0: /* boot and elapsed time alone never write */
  for(unsigned t=0;t<86400000;t+=60000)tick(t);
  assert(!erases&&!programs);break;
 case 1: /* repeated VIA EEPROM updates/imports remain RAM */
  for(unsigned t=0;t<600000;t+=1000){edit(t%255);tick(t);}
  tick(86400000);assert(!erases&&!programs);state();assert(reply[9]);break;
 case 2: /* RGB edits, legacy automatic-toggle and custom-save cannot write */
  cmd(5,1);cmd(2,1);rgb[3]=10;tick(250);
  memset(reply,0,32);reply[0]=9;reply[1]=2;ducky_settings_command(reply,32);assert(reply[0]==9);
  tick(86400000);assert(!erases&&!programs);state();assert(!reply[8]&&!reply[11]);break;
 case 3: /* exactly one manual transaction; no repeated background writes */
  edit(2);rgb[3]=9;save();assert(erases==2);edit(3);tick(86400000);assert(erases==2);break;
 case 4: { /* identical Save never erases/programs again */
  save();unsigned before=programs;save();assert(state()==4&&erases==2&&programs==before);break;}
 case 5: /* Restore requires no arm, changes RAM only */
  edit(8);rgb[3]=10;cmd(3,1);tick(1);
  assert(state()==9&&resets==1&&rgb[3]==9&&rgb[7]==9&&rgb[8]==90&&!erases&&!programs&&reply[9]);break;
 case 6: { /* unsaved defaults must not replace previous saved snapshot */
  edit(42);rgb[3]=9;save();cmd(3,1);tick(1);assert(state()==9&&erases==2);
  assert(ducky_store_load()>=0);ducky_settings_init();uint8_t v=0;
  eeprom_read_block(&v,(void *)100,1);assert(v==42&&rgb[3]==9&&erases==2);break;}
 case 7: { /* defaults persist only after explicit Save */
  edit(42);rgb[3]=9;save();cmd(3,1);tick(1);save();assert(erases==4);
  edit(55);rgb[3]=10;assert(ducky_store_load()>=0);ducky_settings_init();uint8_t v=1;
  eeprom_read_block(&v,(void *)100,1);assert(v==0&&rgb[3]==9);break;}
 case 8: /* pending manual Save waits for USB, keys and CM editor */
  edit(1);cmd(1,1);connected=false;tick(6000);assert(!erases);
  connected=true;keys=1;tick(10000);assert(!erases);
  keys=0;editing=true;tick(12000);assert(!erases);
  editing=false;tick(15000);assert(erases==2);break;
 case 9: /* failed write requires a fresh explicit Save */
  edit(1);fail_write=true;cmd(1,1);tick(1);assert(state()==5&&erases==1);
  tick(86400000);assert(erases==1);fail_write=false;save();assert(state()==3);break;
 case 10: /* unknown partition is never erased */
  flash[0]=0;edit(1);cmd(1,1);tick(1);assert(state()==6&&!erases);break;
 case 11: /* target mismatch is never written */
  *(uint32_t *)0x5000c014=0;edit(1);cmd(1,1);tick(1);assert(state()==7&&!erases);break;
 case 12: /* busy duplicate Save ACK cannot change queued RAM-only reset */
  keys=1;cmd(3,1);cmd(1,1);tick(20);assert(!erases&&state()==2);
  keys=0;tick(21);assert(!erases&&state()==9&&resets==1);break;
 case 13: /* legacy test10.1 ON snapshot cannot enable automatic writes */
  rgb[3]=9;save();ducky_store_restore_word(DUCKY_EEPROM_SIZE+24,0xa1);
  suspended=true;assert(ducky_store_save()==1);suspended=false;
  assert(ducky_store_load()>=0);ducky_settings_init();state();assert(!reply[8]&&rgb[3]==9);
  edit(44);rgb[3]=5;tick(250);tick(86400000);assert(erases==4);break;
 case 14: /* legacy test10 snapshot imports, without startup rewrite */
  edit(42);rgb[3]=6;save();ducky_store_restore_word(DUCKY_EEPROM_SIZE+24,0);
  suspended=true;assert(ducky_store_save()==1);suspended=false;
  assert(ducky_store_load()>=0);ducky_settings_init();state();assert(!reply[8]&&!reply[9]&&rgb[3]==6);
  tick(86400000);assert(erases==4);break;
 case 15: /* ordinary QMK eeconfig initialization still only mutates RAM */
  eeconfig_init();tick(86400000);assert(!erases&&!programs);break;
 default:abort();
 }
 printf("Persistence controller case %d passed\n",test);return 0;
}
