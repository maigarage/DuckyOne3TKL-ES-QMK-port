#!/usr/bin/env python3
"""Read-only VIA diagnostics for the safety-enabled port. Does not enter bootloader or flash."""
# SPDX-License-Identifier: GPL-2.0-or-later
import json
NAMES=['RSTSTS','BODCTL','PORCTL','WDT_CTL','CLKSEL0','CLKSEL1','CLKDIV0','RGB_STATUS']
REASONS = {0:'No latched RGB fault',1:'Watchdog reset flag present at RGB startup',
 2:'CPU lockup reset flag present at RGB startup',3:'Watchdog initialization failed',
 4:'Foreground heartbeat expired',5:'RGB scan timer overrun',6:'Invalid scan buffer or bank state',
 7:'Invalid render buffer state',8:'Invalid editor or effect state',9:'Declared USB send exceeded its scan budget'}
def read_value(dev,index,optional=False):
 req=bytes([8,1,index,0])+bytes(28)
 if dev.write(b'\0'+req)!=33:raise RuntimeError('Incomplete HID write')
 r=bytes(dev.read(32,2000))
 if len(r)!=32:raise RuntimeError('Incomplete or timed-out diagnostics response')
 if optional and r[0]==255:return None
 if r[:3]!=req[:3]:raise RuntimeError('Incompatible response, or VIA is using the interface')
 return int.from_bytes(r[4:8],'little')
def collect(dev):
 registers={name:read_value(dev,i) for i,name in enumerate(NAMES)}
 state=registers['RGB_STATUS'];flags=registers['RSTSTS']
 result={'registers':{n:hex(v) for n,v in registers.items()},'rgb_fault':bool(state&1),
  'rgb_running':bool(state&2),'ceiling_percent':(state>>8)&255,
  'reset_flags':{'watchdog':bool(flags&4),'low_voltage':bool(flags&8),'brown_out':bool(flags&16),
   'software_system':bool(flags&32),'cpu_lockup':bool(flags&256)},'hardware_measurement':False,
  'note':'Reset flags can accumulate; they do not establish event order. Register readings only; current, voltage and temperature are not measured.'}
 extended=read_value(dev,8,optional=True)
 if extended is not None and extended>>24 in (1,2):
  reason=extended&255
  result.update(diagnostics_version=extended>>24,rgb_fault_reason_code=reason,
   rgb_fault_reason=REASONS.get(reason,'Unknown reason'),
   usb_pause_count=read_value(dev,9),scan_sequence=read_value(dev,10))
  if extended>>24==2:
   result.update(usb_wait_count=read_value(dev,11),usb_wait_peak_scans=read_value(dev,12),
    usb_event_count=read_value(dev,13),usb_last_event=read_value(dev,14))
 else:
  result.update(diagnostics_version=0,rgb_fault_reason='Not available in this firmware revision')
 return result
def main():
 import hid
 candidates=[d for d in hid.enumerate(0x3233,0x8311) if d.get('usage_page')==0xff60 and d.get('usage')==0x61]
 if len(candidates)!=1:raise RuntimeError('Expected one Ducky VIA interface. Close VIA and ensure the safety-enabled port is running.')
 dev=hid.device();dev.open_path(candidates[0]['path'])
 try:
  print(json.dumps(collect(dev),indent=2))
 finally:dev.close()
if __name__=='__main__':main()
