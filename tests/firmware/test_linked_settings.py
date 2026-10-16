# SPDX-License-Identifier: GPL-2.0-or-later
"""Manual-only settings protocol against actual linked ARM code."""
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
with Path('firmware/qmk.elf').open('rb') as f:
    e=ELFFile(f)
    symbols={s.name:s['st_value'] for s in e.get_section_by_name('.symtab').iter_symbols()}
    segments=[(s['p_vaddr'],s.data()) for s in e.iter_segments() if s['p_type']=='PT_LOAD' and s['p_filesz']]
class Device:
    def __init__(self):
        self.now=0
        self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        self.u.mem_map(0,0x20000);self.u.mem_map(0x20000000,0x5000)
        for a,b in segments:self.u.mem_write(a,b)
        self.u.hook_add(UC_HOOK_CODE,self.code)
    def code(self,u,a,size,data):
        if a==(symbols['timer_read32']&~1):
            u.reg_write(UC_ARM_REG_R0,self.now)
            u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
    def command(self,cmd,id=0,value=0,n=32):
        p=0x20004c00
        self.u.mem_write(p,bytes([cmd,2,id,value])+bytes(28))
        self.u.reg_write(UC_ARM_REG_R0,p);self.u.reg_write(UC_ARM_REG_R1,n)
        self.u.reg_write(UC_ARM_REG_SP,0x20004ff0);self.u.reg_write(UC_ARM_REG_LR,0x1d001)
        self.u.emu_start(symbols['ducky_settings_command']|1,0x1d000,count=100000)
        assert self.u.reg_read(UC_ARM_REG_PC)==0x1d000
        return bytes(self.u.mem_read(p,32))
checks=[]
d=Device();s=d.command(8);assert s[4:6]==bytes([10,3]) and s[8]==s[11]==0
checks.append('protocol revision 3 advertises auto-save off')
for setting in (2,5):
    d=Device();assert d.command(7,setting,1)[0]==7
    d.now=86400000;s=d.command(8);assert s[7]==s[8]==s[11]==0
    assert d.command(8,5)[3]==0
checks.append('legacy Arm and auto-save ON do not queue an operation')
d=Device();assert d.command(7,3,1)[:4]==bytes([7,2,3,1]);s=d.command(8);assert s[3]==2 and s[11]==2
assert d.command(7,1,1)[0]==7 and d.command(8)[11]==2
checks.append('one Restore button queues RAM reset; busy duplicate cannot replace it with flash Save')
d=Device();d.command(7,1,1);s=d.command(8);assert s[3]==2 and s[11]==1
checks.append('explicit Save queues the sole flash-writing action')
d=Device();assert d.command(9)[0]==9 and d.command(8)[11]==0
assert d.command(7,99,1)[0]==255
checks.append('generic custom-save is a no-op; unsupported controls still rejected')
print(json.dumps({'result':'PASS','checks':checks,'hardware_validated':False},indent=2))
