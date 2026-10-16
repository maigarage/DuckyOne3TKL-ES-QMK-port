# SPDX-License-Identifier: GPL-2.0-or-later
import sys
WORK = __import__("pathlib").Path(sys.argv[1])
from unicorn import *
from unicorn.arm_const import *
import struct,json
from pathlib import Path
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.mem_map(0,0x20000);u.mem_map(0x20000000,0x10000);u.mem_write(0,(WORK / 'vendor/Ducky-One3-TKL-RGB-1.16-APROM.bin').read_bytes());u.mem_write(0x20000000,(WORK / 'vendor/stock-engine-initial.bin').read_bytes())
u.mem_write(0x20001794,b''.join(struct.pack('<3H',i+1,i+1,i+1) for i in range(102)))
u.reg_write(UC_ARM_REG_SP,0x2000f000);u.reg_write(UC_ARM_REG_LR,0x1ff01);u.reg_write(UC_ARM_REG_R0,0x20001794);u.reg_write(UC_ARM_REG_R1,0);u.reg_write(UC_ARM_REG_R2,0);u.reg_write(UC_ARM_REG_R3,0);u.mem_write(0x2000f000,struct.pack('<3I',0x20001370,0x20007000,0));u.emu_start(0x3cd1,0x1ff00,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0x1ff00
route={ (0,1):(0,16),(3,14):(1,16),(3,15):(2,16),(4,14):(4,15),(4,15):(5,16) }
for r in range(6):
 for c in range(16):
  rr,cc=route.get((r,c),(r,c));got=struct.unpack('<3H',u.mem_read(0x20000e30+672+r*96+c*6,6));assert got==(rr*17+cc+1,)*3,(r,c,got)
print(json.dumps({'result':'PASS','source':'V1.16 renderer 0x3cd0 executed with unique tagged pixels','checked_slots':96,'exceptions':[{'wire':[r,c],'geometry':list(v)} for (r,c),v in route.items()]},indent=2))
