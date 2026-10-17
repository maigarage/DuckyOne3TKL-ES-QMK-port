# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded USB-wait and configuration-stability tests, actual ARM instructions."""
exec(open('validation/test_usb_shutdown.py').read().split('checks=[]')[0])
checks=[]
for linked in (False,True):
    S=linked_symbols if linked else standalone_symbols
    d=fresh();d.w=[];d.call('ducky_usb_wait_begin')
    assert d.u.reg_read(UC_ARM_REG_R0)==1
    feeds=0
    for i in range(100):
        d.frame();assert not d.get('fault') and any(d.gates.values())
        feeds+=sum(a==0x40004008 and v==0x5aa5 for a,v in d.w)
    assert feeds==100 and word(d,S['usb_wait_peak'])==100
    d.call('ducky_usb_wait_end');d.frame();assert not d.get('fault')
    assert not any(a==0x40004008 for a,v in d.w)
    checks.append('100-scan legitimate wait: healthy scan feeds unchanged WDT; end revokes lease')
    d=fresh();d.call('ducky_usb_wait_begin')
    for i in range(80):d.frame()
    d.call('ducky_usb_wait_begin');assert d.u.reg_read(UC_ARM_REG_R0)==0
    for i in range(45):d.frame()
    assert not d.get('fault')
    d.frame();assert d.get('fault') and d.get('fault_reason')==9
    assert not any(d.gates.values()) and not any(a==0x40004008 for a,v in d.w)
    assert word(d,0x40004000)&0x80
    checks.append('126th scan expires wait; nested/retry entry cannot renew it')
    d=fresh();d.call('ducky_usb_wait_begin');d.overrun=True;d.frame()
    assert d.get('fault_reason')==5 and not any(a==0x40004008 for a,v in d.w)
    checks.append('overrun still cuts output before any wait-lease WDT feed')
    d=fresh();d.call('ducky_usb_wait_begin');usb(d,False);d.frame();stopped(d)
    assert not d.get('usb_wait_active')
    d.call('ducky_usb_wait_end');stopped(d)
    checks.append('USB loss cancels wait only after hardware is safely off')
    d=fresh();d.call('ducky_rgb_suspend');d.call('ducky_watchdog_start')
    d.call('ducky_usb_wait_begin');assert d.u.reg_read(UC_ARM_REG_R0)==0
    assert word(d,0x40004000)&0x80
    checks.append('flash WDT cannot receive a transport wait lease')
    # No IRQ execution means no WDT feed, even when a lease exists.
    d=fresh();d.w=[];d.call('ducky_usb_wait_begin');d.call('ducky_usb_wait_end')
    assert not any(a==0x40004008 for a,v in d.w)
    checks.append('declaring a wait does not feed WDT without scan progress')
    # Stable configuration is required after reset/suspend, including churn
    # that occurs between foreground observations of USB_ACTIVE.
    d=fresh();usb(d,False);d.frame();stopped(d)
    usb(d,True);d.render(3000);assert not d.get('running')
    d.render(3499);assert not d.get('running')
    d.call('ducky_rgb_usb_event',1);d.render(3500)
    d.render(3999);assert not d.get('running')
    d.render(4000);assert d.get('running') and not d.get('fault')
    checks.append('500ms stability; intervening USB reset restarts the window')
    # Existing heartbeat and boot-reset guards are retained.
    d=fresh()
    for i in range(51):d.frame()
    assert d.get('fault_reason')==4 and not any(d.gates.values())
    checks.append('undeclared main-loop stall still faults at scan 51')
print(json.dumps({'result':'PASS','checks':checks,'targets':['standalone ARM','final linked firmware'],
 'hardware_validated':False,'limitations':'Register model; no physical BIOS, power rail or watchdog oscillator timing'},indent=2))
