# SPDX-License-Identifier: GPL-2.0-or-later
"""Check USB suspend/resume control flow in the exact private Ducky 1.16 image.
The two hardware transition routines and 0x31b8 are intercepted, not emulated.
"""
from pathlib import Path
import hashlib,json,struct
from unicorn import *
from unicorn.arm_const import *
b=Path('analysis/Ducky-One3-TKL-RGB-1.16-APROM.bin').read_bytes()
assert hashlib.sha256(b).hexdigest()=='e04458f82c1a14baa1b77fd4d63c1b9046a93fd2ed6efe5fc778fbbf87d72c59'
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
for a,n in [(0,0x10000),(0x20000000,0x10000),(0x40060000,0x1000)]:u.mem_map(a,n)
u.mem_write(0,b)
seen=[]
def hook(u,a,size,data):
    if a in (0x3ae4,0x3b98,0x31b8):
        seen.append(hex(a));u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
def call(a):
    u.reg_write(UC_ARM_REG_SP,0x2000f000);u.reg_write(UC_ARM_REG_LR,0xf001)
    u.emu_start(a|1,0xf000,count=20000);assert u.reg_read(UC_ARM_REG_PC)==0xf000
def write(a,v):u.mem_write(a,struct.pack('<I',v))
assert struct.unpack_from('<I',b,39*4)[0]==0xa155
write(0x40060004,1);write(0x40060010,0x92);call(0xa154)
assert u.mem_read(0x20002e41,1)==b'\1'
assert not int.from_bytes(u.mem_read(0x40060010,4),'little')&0x10
call(0x33f4);assert seen==['0x3ae4','0x31b8']
write(0x40060004,1);write(0x40060010,0x84);call(0xa154)
assert u.mem_read(0x20002e41,1)==b'\0'
assert int.from_bytes(u.mem_read(0x40060010,4),'little')&0x90==0x90
call(0x33f4);assert seen==['0x3ae4','0x31b8','0x3b98','0x31b8']
# A bus reset and BOOT/REPORT protocol selection are not suspend transitions.
seen.clear()
write(0x40060004,1);write(0x40060010,0x91);call(0xa154)
assert u.mem_read(0x20002e41,1)==b'\0'
call(0x33f4);assert seen==[]
setup=struct.unpack_from('<I',b,0x9d80)[0]
assert setup==0x20000314
for protocol in (0,1,0):
    u.mem_write(setup,bytes([0x21,0x0b,protocol,0,0,0,0,0]))
    call(0xa31c)
    assert u.mem_read(0x20002e48,1)==bytes([protocol])
    call(0x33f4);assert seen==[]
print(json.dumps({'result':'PASS','usb_irq':'0xa154','suspend_flag':'0x20002e41',
 'foreground_dispatch':'0x33f4','suspend_routine':'0x3ae4','resume_routine':'0x3b98',
 'bus_reset_and_boot_report_do_not_select_suspend':True,
 'hardware_transition_routines_executed':False,'hardware_validated':False},indent=2))
