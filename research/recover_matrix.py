# SPDX-License-Identifier: GPL-2.0-or-later
"""Evaluate the GPIO initialization block 0x4cfc..0x4e2a without hardware access.
Requires Capstone. Stops on unsupported instructions. Addresses are V1.16-specific.
Pass the private workspace path as the only argument.
"""
import sys
WORK = __import__("pathlib").Path(sys.argv[1])
import struct,json,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import ARM_OP_IMM,ARM_OP_REG,ARM_OP_MEM
b=(WORK / 'vendor/Ducky-One3-TKL-RGB-1.16-APROM.bin').read_bytes()
assert hashlib.sha256(b).hexdigest()=='e04458f82c1a14baa1b77fd4d63c1b9046a93fd2ed6efe5fc778fbbf87d72c59'
d=Cs(CS_ARCH_ARM,CS_MODE_THUMB);d.detail=True
r={f'r{i}':0 for i in range(13)};r.update(sp=0x20004f00,lr=0)
m={}
def read(a,n):
 if 0<=a<=len(b)-n:return int.from_bytes(b[a:a+n],'little')
 return sum(m.get(a+i,0)<<(8*i) for i in range(n))
def write(a,v,n):
 assert 0x20000000<=a<0x20005000
 for i in range(n):m[a+i]=(v>>(8*i))&255
def val(o):return o.imm if o.type==ARM_OP_IMM else r[d.reg_name(o.reg)]
for x in d.disasm(b[0x4cfc:0x4e2a],0x4cfc):
 o=x.operands;mn=x.mnemonic
 if mn=='push':
  r['sp']-=4*len(o)
  for j,z in enumerate(o):write(r['sp']+j*4,val(z),4)
 elif mn in ['mov','movs']:r[x.reg_name(o[0].reg)]=val(o[1])
 elif mn in ['add','adds','sub','subs']:
  target=x.reg_name(o[0].reg);a=val(o[1]) if len(o)==3 else r[target];v=val(o[-1]);r[target]=a+v if mn.startswith('add') else a-v
 elif mn in ['ldr','str','strb','strh']:
  mem=o[1].mem;base=x.reg_name(mem.base)
  a=(((x.address+4)&~3) if base=='pc' else r[base])+mem.disp
  if mn=='ldr':r[x.reg_name(o[0].reg)]=read(a,4)
  else:write(a,val(o[0]),{'str':4,'strb':1,'strh':2}[mn])
 else:raise RuntimeError((hex(x.address),mn,x.op_str))
base=0x20002944
pins=[]
for i in range(22):
 a=base+i*8;port=read(a+4,1);pin=read(a+5,1)
 assert read(a,4)==0x50004000+port*0x40
 assert port<6 and pin<16
 pins.append(f'P{chr(65+port)}{pin}')
result={'source_sha256':hashlib.sha256(b).hexdigest(),'method':'bounded straight-line static evaluation; no hardware', 'init_block':'0x4cfc..0x4e2a','scan_function':'0x4f4c','rows':pins[16:],'columns':pins[:16],'row_count':6,'column_count':16,'scan_behavior':'one row low, columns read via GPIO alias, row restored high','physical_key_mapping':'not yet recovered','hardware_validation':False}
print(json.dumps(result,indent=2))
(WORK / 'vendor/matrix-recovered.json').write_text(json.dumps(result,indent=2)+'\n')
