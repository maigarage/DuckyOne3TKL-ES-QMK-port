# SPDX-License-Identifier: GPL-2.0-or-later
"""Execute real ARM RGB code with USB transitions and delayed foreground work.
Not a real-time/electrical model. WDT timing is represented by its enable bit.
"""
exec(open('validation/model.py').read())
from elftools.elf.elffile import ELFFile
standalone_symbols = S.copy()
with open('firmware/qmk.elf', 'rb') as f:
    elf = ELFFile(f)
    linked_symbols = {s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    linked_segments = [(s['p_vaddr'],s.data()) for s in elf.iter_segments()
                       if s['p_type']=='PT_LOAD' and s['p_filesz']]

def usb(d, active):
    d.u.mem_write(S['USBD1'] if linked else 0x20007005,
                  bytes([4 if active else 5]) if linked else bytes([0 if active else 1]))

def fresh():
    d=Device()
    if linked:
        d.u.mem_write(0x20000000,bytes(0x10000))
        for a,b in linked_segments:d.u.mem_write(a,b)
        def clock(u,a,size,data):
            if a==(S['timer_read32']&~1):
                u.reg_write(UC_ARM_REG_R0,int.from_bytes(u.mem_read(0x20007000,4),'little'))
                u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
        d.u.hook_add(UC_HOOK_CODE,clock)
    usb(d,True)
    d.render(1500);d.render(2000)
    assert d.get('running') and not d.get('fault')
    return d

def word(d,a):return int.from_bytes(d.u.mem_read(a,4),'little')
def stopped(d):
    assert not any(d.gates.values())
    assert not d.get('running') and not d.get('fault')
    assert word(d,0x40010100)==0
    assert not word(d,0x400400d8)&2 and not word(d,0x40040020)&2
    assert not word(d,0x40004000)&0x80

checks=[]
for linked in (False,True):
    S=linked_symbols if linked else standalone_symbols
    # No foreground work needed to blank rows and disable the RGB watchdog.
    d=fresh();d.frame();usb(d,False);d.frame();stopped(d)
    for i in range(60):d.frame() # Even spurious pending IRQs must remain harmless.
    stopped(d)
    assert word(d,S['usb_pause_count'])==1
    usb(d,True);d.render(120000);d.render(120500);assert d.get('running') and not d.get('fault')
    d.frame();assert any(d.gates.values()) and word(d,0x40004000)&0x80
    checks.append('IRQ-only USB pause, delayed foreground and resume')
    # USB interrupt preempts the serial transfer; never enable its bank afterward.
    d=fresh();changed=[False]
    def mid_transfer(u,access,a,size,v,data):
        if a==0x50004280 and v and not changed[0]:changed[0]=True;usb(d,False)
    h=d.u.hook_add(UC_HOOK_MEM_WRITE,mid_transfer)
    d.overrun=True;d.frame();d.u.hook_del(h)
    assert changed[0];stopped(d)
    checks.append('USB loss during transfer takes priority over overrun')
    # Repeated cycles, duplicate wake callbacks and uint32 millisecond wrap.
    d=fresh()
    for n in range(20):
        usb(d,False);d.frame();stopped(d)
        usb(d,True);d.render(3000+n*1000);d.render(3500+n*1000);d.frame()
        d.w=[];d.call('ducky_rgb_resume');d.render(3501+n*1000)
        assert d.get('running') and not any(a==0x40004000 for a,v in d.w)
    assert word(d,S['usb_pause_count'])==20
    d.render(0xffffffff);d.frame();d.w=[];d.render(0)
    assert (0x40004008,0x5aa5) in d.w
    checks.append('20 USB cycles, duplicate wake and timer wrap')
    # Pausing RGB for a Save must not let its scan IRQ disable the flash WDT.
    d=fresh();d.call('ducky_rgb_suspend');d.call('ducky_watchdog_start')
    usb(d,False);d.w=[];d.frame()
    assert word(d,0x40004000)&0x80 and not word(d,S['usb_pause_count'])
    checks.append('flash watchdog ownership retained')
    # Genuine active-USB failures remain latched and keep watchdog recovery.
    d=fresh();d.set('heartbeat',50);d.frame()
    assert d.get('fault') and d.get('fault_reason')==4 and not any(d.gates.values())
    assert word(d,0x40004000)&0x80
    usb(d,False);d.frame();assert word(d,0x40004000)&0x80
    d=fresh();d.overrun=True;d.frame()
    assert d.get('fault') and d.get('fault_reason')==5 and not any(d.gates.values())
    checks.append('real heartbeat and overrun faults remain latched')
print(json.dumps({'result':'PASS','checks':checks,'executed':'standalone ARM and linked firmware',
                  'hardware_validated':False},indent=2))
