from unicorn import *
from unicorn.arm_const import *
from pathlib import Path
import struct,json
S={a[2]:int(a[0],16) for l in Path('validation/rgb.nm').read_text().splitlines() if len(a:=l.split())==3}
rows=[0x50004298,0x50004294,0x500042dc,0x500042fc,0x500042f8,0x500042f4,0x50004348]
class Device:
 def __init__(self):
  self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);self.w=[];self.instructions=0;self.overrun=False;self.gates={x:0 for x in rows};self.gates[0x50004348]=1;self.max_on=0
  for a,n in [(0,0x10000),(0x20000000,0x10000),(0x50000000,0x10000),(0x40040000,0x1000),(0x40010000,0x1000),(0x40004000,0x1000),(0xe000e000,0x1000)]:self.u.mem_map(a,n)
  self.u.mem_write(0x1000,Path('validation/rgb-text.bin').read_bytes());self.u.mem_write(0x20000000,Path('validation/rgb-data.bin').read_bytes())
  self.u.mem_write(0x5000020c,struct.pack("<I",0x3f))
  self.u.hook_add(UC_HOOK_MEM_WRITE,self.write);self.u.hook_add(UC_HOOK_MEM_READ,self.read);self.u.hook_add(UC_HOOK_CODE,self.code)
 def write(self,u,access,a,size,v,_):
  if a>=0x40000000:self.w.append((a,v))
  # Stock keeps the preceding row active until the final column.
  if a in rows:self.gates[a]=v;self.max_on=max(self.max_on,sum(self.gates.values()));assert self.max_on<=1
 def read(self,u,access,a,size,v,_):
  if a==0x40010108:u.mem_write(a,struct.pack('<I',int(self.overrun)))
 def code(self,*_):self.instructions+=1
 def set(self,name,v):self.u.mem_write(S[name],bytes([v]))
 def get(self,name):return self.u.mem_read(S[name],1)[0]
 def call(self,name,a=0,b=0):
  u=self.u;u.reg_write(UC_ARM_REG_SP,0x2000f000);u.reg_write(UC_ARM_REG_LR,0xf001);u.reg_write(UC_ARM_REG_R0,a);u.reg_write(UC_ARM_REG_R1,b)
  self.instructions=0;u.emu_start(S[name]|1,0xf000,count=200000);assert u.reg_read(UC_ARM_REG_PC)==0xf000
  return self.instructions
 def time(self,t):self.u.mem_write(0x20007000,struct.pack('<I',t))
 def key(self,k,pressed=True,r=2,c=3):self.u.mem_write(0x20008000,struct.pack('<BBHBB',c,r,0,1,int(pressed)));self.call('ducky_rgb_process',k,0x20008000)
 def frame(self):
  self.w=[];count=self.call('Vector64');frames=decode(self.w);return frames,count
 def render(self,t):self.time(t);self.call('ducky_caps_task')
 def settle(self,t):
  self.render(t)
  out=[]
  for i in range(7):
   f,n=self.frame();out+=f
  return out

def decode(writes):
 clk=le=data=0;bits=[];les=[]
 for a,v in writes:
  if a==0x5000428c:data=v
  if a==0x50004288:le=v
  if a==0x50004280:
   if v and not clk:bits.append(data);les.append(le)
   clk=v
 assert len(bits)%773==0,len(bits)
 frames=[]
 for start in range(0,len(bits),773):
  frame=[]
  for col in range(16):
   off=start+col*48;assert les[off:off+48]==[0]*47+[1]
   vv=[]
   for k in range(3):
    v=0
    for bit in bits[off+k*16:off+(k+1)*16]:v=v*2+bit
    vv.append(v)
   frame.append(vv)
  assert les[start+768:start+773]==[0,0,1,1,1]
  frames.append(frame)
 return frames

