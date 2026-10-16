// SPDX-License-Identifier: GPL-2.0-or-later
/* Fault injection uses the ACTUAL portable transaction implementation. */
#include "ducky_store.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint32_t flash[2*DUCKY_STORE_BANK_SIZE/4];
static uint32_t saved[2*DUCKY_STORE_BANK_SIZE/4];
static uint32_t source[DUCKY_STORE_PAYLOAD/4],loaded[DUCKY_STORE_PAYLOAD/4];
static int left=-1, operations;
static bool torn;
static unsigned index_of(uint32_t a) {
 assert(a>=DUCKY_STORE_BASE && a<DUCKY_STORE_BASE+sizeof flash && !(a&3));
 return (a-DUCKY_STORE_BASE)/4;
}
uint32_t ducky_flash_read(uint32_t a){return flash[index_of(a)];}
bool ducky_flash_program(uint32_t a,uint32_t v) {
 unsigned n=index_of(a);operations++;
 if(left==0){if(torn)flash[n]&=v|0xffff0000u;return false;}
 if(left>0)left--;
 assert((flash[n]&v)==v);flash[n]&=v;return true;
}
bool ducky_flash_erase(uint32_t a) {
 unsigned n=index_of(a);assert(!(a%DUCKY_STORE_PAGE_SIZE));operations++;
 if(left==0){if(torn)memset(flash+n,0xff,DUCKY_STORE_PAGE_SIZE/2);return false;}
 if(left>0)left--;
 memset(flash+n,0xff,DUCKY_STORE_PAGE_SIZE);return true;
}
uint32_t ducky_store_source_word(uint32_t off){assert(off<sizeof source);return source[off/4];}
void ducky_store_restore_word(uint32_t off,uint32_t v){assert(off<sizeof loaded);loaded[off/4]=v;}
static void fill(uint32_t salt){for(unsigned i=0;i<sizeof source/4;i++)source[i]=salt+i;}
int main(void) {
 memset(flash,0xff,sizeof flash);fill(0x12340000);
 assert(ducky_store_load()==-1 && ducky_store_save()==1);
 assert(ducky_store_load()==0 && !memcmp(source,loaded,sizeof source));
 operations=0;assert(ducky_store_save()==2 && operations==0);
 memcpy(saved,flash,sizeof flash);fill(0x56780000);operations=0;
 assert(ducky_store_save()==1);int total=operations;
 for(int cut=0;cut<total;cut++)for(int partial=0;partial<2;partial++) {
  memcpy(flash,saved,sizeof flash);left=cut;torn=partial;
  assert(ducky_store_save()==-1);
  assert(ducky_store_load()==0);
  for(unsigned i=0;i<sizeof loaded/4;i++)assert(loaded[i]==0x12340000u+i);
 }
 left=-1;torn=false;memcpy(flash,saved,sizeof flash);
 assert(ducky_store_save()==1 && ducky_store_load()==1 && !memcmp(source,loaded,sizeof source));
 // Corruption in header, CRC, payload or seal falls back to intact prior bank.
 memcpy(saved,flash,sizeof flash);
 for(unsigned offset=0;offset<(32+DUCKY_STORE_PAYLOAD)/4;offset++) {
  memcpy(flash,saved,sizeof flash);flash[DUCKY_STORE_BANK_SIZE/4+offset]^=1;
  assert(ducky_store_load()==0);
 }
 memset(flash,0xff,sizeof flash);flash[1]=0x87654321;operations=0;
 assert(ducky_store_save()==-2 && operations==0); // never erase unknown data
 // First save interrupted at every operation never exposes a partial snapshot.
 for(int cut=0;cut<total;cut++) {
  memset(flash,0xff,sizeof flash);left=cut;
  assert(ducky_store_save()==-1 && ducky_store_load()==-1);
 }
 left=-1;memset(flash,0xff,sizeof flash);fill(1);assert(ducky_store_save()==1);
 fill(0);assert(ducky_store_save()==1); // saving defaults is a normal transaction
 assert(ducky_store_load()==1 && !memcmp(source,loaded,sizeof source));
 printf("PASS: %d cut points, torn words/pages, corruption fallback, unknown-region refusal, unchanged-save wear avoidance, reset transaction\n",total);
}
