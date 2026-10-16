# SPDX-License-Identifier: GPL-2.0-or-later
"""Exercise the actual linked SRAM FMC routine against a register/flash model.
No HID/device access. This is not an electrical or flash-timing validation.
"""
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
with Path('firmware/qmk.elf').open('rb') as stream:
    elf=ELFFile(stream)
    symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    sections=[(s['p_vaddr'],s.data()) for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_filesz']]
assert 0x20000000 <= (symbols['flash_operation'] & ~1) < 0x20005000

class Device:
    def __init__(self,fail=False,stuck=False):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        self.u.mem_map(0,0x20000);self.u.mem_write(0,b'\xff'*0x20000)
        self.u.mem_map(0x20000000,0x5000);self.u.mem_map(0x50000000,0x10000)
        self.u.mem_map(0xe000e000,0x1000);self.u.mem_map(0x40004000,0x1000)
        for address,data in sections:self.u.mem_write(address,data)
        self.put(0x50000000,0x01205212);self.put(0x5000c014,0x33200)
        self.put(0x50000204,0x100);self.ctl=2;self.pending=None;self.commands=[]
        self.fail=fail;self.stuck=stuck;self.busy_instructions=0
        self.u.hook_add(UC_HOOK_MEM_WRITE,self.write)
        self.u.hook_add(UC_HOOK_MEM_READ,self.read)
        self.u.hook_add(UC_HOOK_CODE,self.code)
    def put(self,a,v):self.u.mem_write(a,struct.pack('<I',v))
    def get(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
    def write(self,u,access,a,size,v,data):
        if a==0x5000c000:
            assert not (v & 0x34), 'CONFIG/LDROM/SPROM enable attempted'
            self.ctl=(v&~0x40)|(self.ctl&0x40 if not v&0x40 else 0)
        if a==0x5000c010 and v==1:
            address=self.get(0x5000c004);command=self.get(0x5000c00c)
            assert 0x1e000<=address<0x20000 and command in (0x21,0x22)
            assert self.ctl&9==9
            self.pending=(address,command,self.get(0x5000c008),3)
            self.commands.append((address,command))
    def code(self,u,a,size,data):
        if self.pending:
            assert 0x20000000<=a<0x20005000, 'Instruction fetch from flash while busy'
            self.busy_instructions+=1
    def read(self,u,access,a,size,v,data):
        if a==0x5000c000:self.put(a,self.ctl)
        if a==0x5000c010 and self.pending:
            address,command,value,remaining=self.pending
            if self.stuck:return
            if remaining:
                self.pending=(address,command,value,remaining-1);return
            if self.fail:self.ctl|=0x40
            elif command==0x22:
                assert address%2048==0
                self.u.mem_write(address,b'\xff'*2048)
            else:self.put(address,self.get(address)&value)
            self.pending=None;self.put(a,0)
    def call(self,a,value=0x12345678,erase=False,limit=20000):
        self.u.reg_write(UC_ARM_REG_SP,0x20004f00)
        self.u.reg_write(UC_ARM_REG_LR,0x1d001)
        for reg,v in [(UC_ARM_REG_R0,a),(UC_ARM_REG_R1,value),(UC_ARM_REG_R2,int(erase))]:self.u.reg_write(reg,v)
        self.u.emu_start(symbols['flash_operation']|1,0x1d000,count=limit)
        return self.u.reg_read(UC_ARM_REG_R0)

checks=[]
for address in (0x1e000,0x1effc,0x1f000,0x1fffc):
    d=Device();assert d.call(address)==1 and d.get(address)==0x12345678
    assert d.ctl==2 and d.get(0x50000100)==0 and d.get(0x50000204)==0x100
    assert d.busy_instructions>0
checks.append('program/read-back at both bank boundaries; relock, clock and boot selection preserved')
d=Device();d.u.mem_write(0x1f800,bytes(2048));assert d.call(0x1f800,erase=True)==1
assert bytes(d.u.mem_read(0x1f800,2048))==b'\xff'*2048
checks.append('2048-byte aligned page erase')
for a,e in [(0,False),(0x1dffc,False),(0x20000,False),(0x100000,True),(0x300000,True),(0x1e001,False),(0x1e004,True)]:
    d=Device();assert d.call(a,erase=e)==0 and not d.commands
checks.append('code, LDROM, CONFIG, out-of-range and unaligned requests refused before FMC trigger')
for register in (0x50000000,0x5000c014):
    d=Device();d.put(register,0);assert d.call(0x1e000)==0 and not d.commands
checks.append('PDID and existing Data Flash boundary fail closed')
d=Device(fail=True);assert d.call(0x1e000)==0 and d.ctl==2
checks.append('FMC failure reported and update permissions closed')
d=Device(stuck=True);d.call(0x1e000,limit=10000)
assert d.pending and 0x20000000<=d.u.reg_read(UC_ARM_REG_PC)<0x20005000
checks.append('busy operation stays in SRAM; hardware watchdog timeout remains a physical test')
print(json.dumps({'result':'PASS','checks':checks,'hardware_validated':False},indent=2))
