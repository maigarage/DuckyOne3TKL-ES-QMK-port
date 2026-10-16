#!/usr/bin/env python3
"""Read-only VIA diagnostics for the safety-enabled port. Does not enter bootloader or flash."""
# SPDX-License-Identifier: GPL-2.0-or-later
import json
import hid
NAMES=['RSTSTS','BODCTL','PORCTL','WDT_CTL','CLKSEL0','CLKSEL1','CLKDIV0','RGB_STATUS']
def main():
 candidates=[d for d in hid.enumerate(0x3233,0x8311) if d.get('usage_page')==0xff60 and d.get('usage')==0x61]
 if len(candidates)!=1:raise RuntimeError('Expected one Ducky VIA interface. Close VIA and ensure the safety-enabled port is running.')
 dev=hid.device();dev.open_path(candidates[0]['path'])
 try:
  result={}
  for i,name in enumerate(NAMES):
   req=bytes([8,1,i,0])+bytes(28)
   if dev.write(b'\0'+req)!=33:raise RuntimeError('Incomplete HID write')
   r=bytes(dev.read(32,2000))
   if len(r)!=32 or r[:3]!=req[:3]:raise RuntimeError('Response is incompatible with this port, or VIA is using the interface')
   result[name]=int.from_bytes(r[4:8],'little')
  state=result['RGB_STATUS']
  print(json.dumps({'registers':{n:hex(v) for n,v in result.items()},'rgb_fault':bool(state&1),'rgb_running':bool(state&2),'ceiling_percent':(state>>8)&255,'hardware_measurement':False,'note':'Register readings only; current, voltage and temperature are not measured.'},indent=2))
 finally:dev.close()
if __name__=='__main__':main()
