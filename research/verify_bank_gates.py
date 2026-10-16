# SPDX-License-Identifier: GPL-2.0-or-later
import sys
WORK = __import__("pathlib").Path(sys.argv[1])
from unicorn import *
from unicorn.arm_const import *
from pathlib import Path
import struct,json
b=(WORK / 'vendor/Ducky-One3-TKL-RGB-1.16-APROM.bin').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
for a,n in [(0,0x10000),(0x20000000,0x10000),(0x50000000,0x10000)]:u.mem_map(a,n)
u.mem_write(0,b)
u.reg_write(UC_ARM_REG_R4,0x50004080);u.reg_write(UC_ARM_REG_R6,0x50004100)
u.emu_start(0x39e9,0x3a3a,count=200)
table=[struct.unpack('<III',u.mem_read(0x20002a5c+i*12,12)) for i in range(7)]
assert table[6]==(0x50004140,5,2)
w=[]
u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,size,v,data:w.append((a,v)))
for old in range(7):
 u.reg_write(UC_ARM_REG_R6,0x20002dd0);u.reg_write(UC_ARM_REG_R7,0)
 u.mem_write(0x20002dd2,bytes([old]));w.clear()
 u.emu_start(0x38f7,0x3912,count=100)
 assert w==[(0x50004200+table[old][1]*64+table[old][2]*4,0)]
for new in range(7):
 u.reg_write(UC_ARM_REG_R6,0x20002dd0);u.reg_write(UC_ARM_REG_R4,1);u.reg_write(UC_ARM_REG_R7,0)
 u.mem_write(0x20002dd3,bytes([new]));w.clear()
 u.emu_start(0x392d,0x394a,count=100)
 assert (0x50004200+table[new][1]*64+table[new][2]*4,1) in w
assert (0xf7ffff7c>>10)&1
print(json.dumps({'result':'PASS','stock_bank_gate_table':table,'pf2_off':'0x38f6..0x3910, old bank6','pf2_on':'0x392c..0x3948, new bank6','observed_config0':'0xf7ffff7c','CIOINI_bit10':1,'header_evidence':'NUC1261.h GPIO.MODE: CIOINI=1 => initial quasi-bidirectional mode; GPIO.DOUT controls output in this mode. Runtime mode after LDROM has not been measured.','hardware_validated':False},indent=2))
