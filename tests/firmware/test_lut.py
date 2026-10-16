from pathlib import Path
import struct,json
from unicorn import *
from unicorn.arm_const import *
from elftools.elf.elffile import ELFFile
u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.mem_map(0,0x20000);u.mem_map(0x20000000,0x10000)
u.mem_write(0,Path('analysis/Ducky-One3-TKL-RGB-1.16-APROM.bin').read_bytes());u.reg_write(UC_ARM_REG_SP,0x20000830)
u.emu_start(0xa7cd,0x9196,count=2000000);assert u.reg_read(UC_ARM_REG_PC)==0x9196
u.reg_write(UC_ARM_REG_R4,0);u.emu_start(0x94b9,0x954e,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x954e
stock=list(struct.unpack('<11H',u.mem_read(0x20001756,22)))
with open('firmware/qmk.elf','rb') as f:
 e=ELFFile(f);a=next(s['st_value'] for s in e.get_section_by_name('.symtab').iter_symbols() if s.name=='ducky_stock_lut')
 seg=next(s for s in e.iter_segments() if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);b=seg.data()[a-seg['p_vaddr']:a-seg['p_vaddr']+22]
port=list(struct.unpack('<11H',b));assert stock==port
print(json.dumps({'result':'PASS','stock_init_executed':True,'stock_lut':stock,'port_lut':port,'nominal_percent':[round(x*100/65535,4) for x in stock],'ceiling90':58981,'note':'digital PWM scale, not measured current or perceived brightness'},indent=2))
