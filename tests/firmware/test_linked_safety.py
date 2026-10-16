exec(open('validation/model.py').read())
from elftools.elf.elffile import ELFFile
elfpath=Path('firmware/qmk.elf')
with elfpath.open('rb') as f:
 elf=ELFFile(f);S={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()};segs=[(s['p_vaddr'],s.data()) for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_filesz']]
def device():
 d=Device()
 for a,b in segs:d.u.mem_write(a,b)
 for a in rows:d.gates[a]=0
 d.set('running',1);d.set('fault',0);d.set('active',0);d.set('pending',255);d.set('bank',6);d.set('heartbeat',0)
 d.u.mem_write(S['USBD1'],b'\4')
 d.u.mem_write(S['pixels'],b'\xff'*1344)
 return d
checks=[];counts=[]
for cap in [0,25,80,90,255]:
 d=device();d.set('max_brightness_percent',cap);bound=min(cap,90)*65535//100
 for bank in range(7):
  frames,n=d.frame();counts.append(n)
  assert all(v<=bound for f in frames for px in f for v in px)
  assert sum(d.gates.values())==1
 checks.append('7 actual linked banks bounded at '+str(cap))
# Emergency entry is stackless: SP deliberately points outside all mapped RAM.
for name in ['HardFault_Handler','Vector44','ducky_safety_halt','_unhandled_exception']:
 d=device();d.frame();d.w=[];d.u.reg_write(UC_ARM_REG_SP,0xdead0000)
 d.u.emu_start(S[name]|1,0xf000,count=1000)
 assert not any(d.gates.values()) and (0x5000429c,1) in d.w
 checks.append(name+' stackless cutoff')
d=device();d.u.mem_write(S['USBD1'],b'\5');d.call('Vector64');assert not any(d.gates.values());checks.append('suspended USB blocks linked IRQ')
d=device();d.overrun=True;d.frame();assert d.get('fault') and not any(d.gates.values());checks.append('linked overrun cutoff')
# Watchdog setup and feeding are actual release routines, register-level model only.
d=device();d.call('ducky_watchdog_start');assert d.u.reg_read(UC_ARM_REG_R0)==1
assert int.from_bytes(d.u.mem_read(0x40004000,4),'little')==0x800003c2
assert int.from_bytes(d.u.mem_read(0x50000214,4),'little')&3==3
assert int.from_bytes(d.u.mem_read(0x50000100,4),'little')==0
checks.append('linked watchdog LIRC/1024 ticks/reset/IRQ setup and relock')
# ELF vectors must point to the strong handler, not the old weak infinite loop.
assert int.from_bytes(d.u.mem_read(12,4),'little')==(S['HardFault_Handler']|1)
assert int.from_bytes(d.u.mem_read(0x44,4),'little')==(S['Vector44']|1)
d=device();d.frame();d.w=[];d.call('ducky_safety_early')
assert not any(d.gates.values()) and (0x5000429c,1) in d.w
assert not any(0x5000c000<=a<0x5000d000 or a in [0x50000018,0x50000024] for a,v in d.w)
assert int.from_bytes(d.u.mem_read(0x50000100,4),'little')==0
checks.append('linked early cutoff/clock-independent GPIO initialization, no FMC/BOD/POR writes')
print(json.dumps({'result':'PASS','checks':checks,'max_irq_instructions':max(counts),'hardware_validated':False,'limitations':'No analog current, real wall-time, WDT oscillator/reset, USB enumeration or full exception-entry stacking modeled'},indent=2))
