#pragma once
#include <stddef.h>
void eeprom_driver_init(void);
void eeprom_read_block(void *,const void *,size_t);
void eeprom_write_block(const void *,void *,size_t);
