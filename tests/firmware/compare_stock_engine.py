"""Compare release-linked relocated RGB instructions against V1.16, no MMIO mapped."""
from pathlib import Path
import struct,json,sys
from unicorn import *
from unicorn.arm_const import *
from elftools.elf.elffile import ELFFile
B=Path('analysis/Ducky-One3-TKL-RGB-1.16-APROM.bin').read_bytes()
RAM=Path('analysis/stock-engine-initial.bin').read_bytes()
I=[0x266,0x26e,0x46c,0x866,0x9e2,0x66e,0xc00,0xdbc,0x110e,0x10a8,0x136c,0x1f4a]
U=[0x266,0x2f8,0x4f0,0x880,0xa18,0x68c,0xc98,0xe4c,0x11ac,0x10a8,0x13fc,0x1ff8]
OFF=[0,0x39,0x3a,0x3b,0x3c,0x38,0x35,0x36,0x34,0,0x37,0x3d]
with open('firmware/qmk.elf','rb') as f:
 elf=ELFFile(f);S={x.name:x['st_value'] for x in elf.get_section_by_name('.symtab').iter_symbols()};segments=[(s['p_vaddr'],s.data()) for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_filesz']]
class Engine:
 def __init__(self,relocated):
  self.u=u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.mem_map(0,0x20000);u.mem_map(0x20000000,0x10000)
  self.base=S['ducky_stock_blob'] if relocated else 0;self.ram=S['ducky_stock_ram'] if relocated else 0x20001754;self.rng=S['ducky_stock_rng'] if relocated else 0x200003a0
  if relocated:
   for a,d in segments:u.mem_write(a,d)
  else:u.mem_write(0,B);u.mem_write(0x48ec,b'\x70\x47')
  u.mem_write(self.ram,RAM[0x1754:0x2e78]);u.mem_write(self.rng,bytes(0x8c));self.count=0;self.max_count=0;self.min_sp=0x2000f000
  u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.access);u.hook_add(UC_HOOK_CODE,self.code)
 def access(self,u,t,a,n,v,_):
  assert self.ram<=a and a+n<=self.ram+0x1724 or self.rng<=a and a+n<=self.rng+0x8c or 0x2000e000<=a and a+n<=0x2000f000 or t==UC_MEM_READ and self.base<=a and a+n<self.base+0x48ee,('out-of-range',hex(a),hex(u.reg_read(UC_ARM_REG_PC)))
 def code(self,u,a,n,_):
  self.count+=1;self.min_sp=min(self.min_sp,u.reg_read(UC_ARM_REG_SP))
  assert any(x<=a-self.base<y for x,y in [(0x266,0x2820),(0x30a8,0x315e),(0x42bc,0x45b2),(0x48ec,0x48ee)]),('excluded code',hex(a-self.base))
 def call(self,a):
  u=self.u;u.reg_write(UC_ARM_REG_SP,0x2000f000);u.reg_write(UC_ARM_REG_LR,0x1ff01);self.count=0;u.emu_start(self.base+a+1,0x1ff00,count=250000);assert u.reg_read(UC_ARM_REG_PC)==0x1ff00;self.max_count=max(self.max_count,self.count)
 def write(self,off,b):self.u.mem_write(self.ram+off,b)
 def state(self):return bytes(self.u.mem_read(self.ram,0x1724))+bytes(self.u.mem_read(self.rng,0x8c))
results=[]
for mode in range(12):
 for case in range(4):
  a,b=Engine(False),Engine(True)
  for e in (a,b):
   e.write(1,bytes([mode]));e.write(0x2c,[bytes([10,10,10]),bytes([0,7,10]),bytes([1,0,4]),bytes([0,0,0])][case])
   if OFF[mode]:e.write(OFF[mode],bytes([[1,6,11,1][case] if mode==10 else [3,7,12,3][case] if mode==11 else [0,4,9,0][case]]))
   e.call(I[mode]);e.call(0x2534)
  assert a.state()==b.state()
  for frame in range(10):
   for e in (a,b):
    if frame%10==0:e.write(0x29f4-0x1754+((frame//10)%6)*17+(frame*7%16),b'\0')
    if frame%10==5:e.write(0x29f4-0x1754+(((frame-5)//10)%6)*17+((frame-5)*7%16),b'\2')
    e.call(U[mode])
   assert a.state()==b.state(),(mode,case,frame)
  results.append({'mode_stock':mode,'case':case,'frames':10,'max_instructions':b.max_count,'max_stack_bytes':0x2000f000-b.min_sp})
 print('PASS original mode',mode,flush=True)
report={'result':'PASS','comparison':'byte-for-byte full effect RAM + RNG state, original vs release-linked relocated code','frames':480,'scenarios':results,'bounds':'all accesses confined to RGB RAM/RNG/stack/code; no MMIO mapped','hardware_validated':False}
Path('validation/stock-parity.json').write_text(json.dumps(report,indent=2))
print('max instructions',max(x['max_instructions'] for x in results),'max stack',max(x['max_stack_bytes'] for x in results))
