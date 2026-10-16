# Use the independently decoded GPIO scan model from test7.
exec(open('validation/model.py').read())
LUT=[0,1024,2048,4096,6656,9216,12288,16384,28672,36864,65535]
def via(d,id,v=None):
 d.u.mem_write(0x20008100,bytes([8 if v is None else 7,0,id,0 if v is None else v])+bytes(28));d.call('via_custom_value_command_kb',0x20008100,32);return d.u.mem_read(0x20008103,1)[0]
def wire(v):
 v=min(v,58981);return [v,v,(v&65534)|(v>>15)]
def tap(d,k,r=2,c=3):d.key(k,True,r,c);d.key(k,False,r,c)
def settle(d,t):
 # consume pending frame, then allow a new foreground render and its latch
 d.settle(t);return d.settle(t+7)
d=Device();d.render(1499);assert not d.w
d.render(1500);assert decode(d.w)==[[[0,0,0]]*16]
frames=settle(d,1510);assert frames[:6]==[[[36864,36864,36865]]*16]*6
# Real eleven digital levels, through the actual serializer (including bit15 rule).
for k in [5,6,7]:via(d,k,10)
for idx,v in enumerate(LUT):
 assert via(d,3,idx)==idx
 frames=settle(d,1600+idx*14)
 assert frames[:6]==[[wire(v)]*16]*6,(idx,frames[0][0])
# All indicator combinations independent of general lighting, entire original range.
for level in range(1,11):
 via(d,8,level)
 for on in [0,1]:
  via(d,1,on)
  for bits in range(8):
   for n,f in enumerate(['ducky_caps_set','ducky_scroll_set','ducky_mouse_set']):d.call(f,(bits>>n)&1)
   f=settle(d,2000+level*500+on*100+bits*14)[6]
   assert f[5:8]==[wire(LUT[level]) if bits&(1<<n) else [0,0,0] for n in range(3)]
   assert all(px==[0,0,0] for i,px in enumerate(f) if i not in [5,6,7])
# VIA set/get ranges, unknown channel/value/short command behavior.
for id,maxv in [(2,11),(3,10),(4,9),(5,10),(6,10),(7,10),(8,10)]:
 via(d,2,8 if id==4 else 0)
 for v in [0,maxv,255]:
  old=via(d,id);via(d,id,v);got=via(d,id)
  assert got==(old if id==2 and v>11 else max(1,min(v,10)) if id==8 else min(v,maxv)),(id,v,got)
for data in [bytes([8,1,3,0]),bytes([8,0,99,0]),bytes([6,0,1,0])]:
 d.u.mem_write(0x20008100,data);d.call('via_custom_value_command_kb',0x20008100,4);assert d.u.mem_read(0x20008100,1)==b'\xff'
# Every effect mode, default and min/max settings; all channels <= master.
via(d,1,1);via(d,3,7)
for mode in range(12):
 via(d,2,mode)
 for v in [0,10]:
  via(d,4,v)
  for k in [5,6,7]:via(d,k,10)
  for i in range(10):
   tap(d,4,r=i%6,c=i%16)
   frames=settle(d,10000+mode*500+v*20+i*14)
   assert all(0<=x<=16384 for f in frames[:6] for px in f for x in px)
# Alt arrows target indicators, plain arrows master.
via(d,3,7);via(d,8,3);d.u.mem_write(0x20007004,b'\x04');tap(d,0x7e06);assert via(d,8)==4 and via(d,3)==7
d.u.mem_write(0x20007004,b'\0');tap(d,0x7e07);assert via(d,3)==6
# Palette selects a stock color and consumes its corresponding release.
via(d,2,0);tap(d,0x7e0b);assert via(d,9)==1
tap(d,4,r=1,c=4);assert d.u.reg_read(UC_ARM_REG_R0)==0
assert via(d,9)==0
# CM1 recording starts after 5s, allows Caps+F5/F6/F7, commits with Caps+ScrLk.
d.time(30000);d.key(0x7e0e);d.render(34999);assert d.get('recording')==0
d.render(35000);assert d.get('recording')==1;d.key(0x7e0e,False)
tap(d,4,r=2,c=3)
d.key(0x39,True,r=3,c=0);tap(d,0x47,r=0,c=15);d.key(0x39,False,r=3,c=0)
assert d.get('recording')==0 and via(d,10)==1
assert struct.unpack('<H',d.u.mem_read(S['zones']+(2*16+3)*2,2))[0]==0x8aaa
# CM2 black key overrides background; CM1 has priority.
d.time(36000);d.key(0x7e0f);d.render(41000);d.key(0x7e0f,False)
d.key(0x39,True,r=3,c=0);tap(d,0x41,r=0,c=9);d.key(0x39,False,r=3,c=0);tap(d,4,r=2,c=3)
d.key(0x39,True,r=3,c=0);tap(d,0x47,r=0,c=15);d.key(0x39,False,r=3,c=0)
via(d,3,7);f=settle(d,42000);assert f[2][3]==[16384,16384,16384]
via(d,10,0);f=settle(d,42100);assert f[2][3]==[0,0,0]
# Timeout discards uncommitted draft.
before=bytes(d.u.mem_read(S['zones'],384));d.time(43000);d.key(0x7e0e);d.render(48000);d.key(0x7e0e,False);tap(d,4,r=2,c=5);d.render(78001)
assert d.get('recording')==0 and bytes(d.u.mem_read(S['zones'],384))==before
# Hold off includes zones and palette. Independent indicators remain active.
d.time(80000);d.key(0x7e05);d.render(83000);d.key(0x7e05,False);assert via(d,1)==0 and via(d,10)==0 and via(d,11)==0
# Suspend/fault cutoff and unchanged clocks/blanking.
d.call('ducky_rgb_suspend');assert not any(d.gates.values());d.call('ducky_rgb_resume');d.render(84000);assert d.get('running')==1
for i in range(51):d.frame()
assert d.get('fault')==1 and not any(d.gates.values())
d2=Device();d2.render(1500);d2.overrun=True;d2.frame();assert d2.get('fault')==1 and not any(d2.gates.values())

# Common hard ceiling applies to every mode and old queued frames, with exact red encoding.
for cap in [0,1,25,50,80,90,100,255]:
 e=Device();e.render(1500)
 assert via(e,12)==90
 via(e,12,cap);bound=min(cap,90)*65535//100
 assert via(e,12)==min(cap,90)
 via(e,3,10);via(e,8,10)
 for key in [5,6,7]:via(e,key,10)
 e.call('ducky_caps_set',1);e.call('ducky_scroll_set',1);e.call('ducky_mouse_set',1)
 for m in range(12):
  via(e,2,m)
  for i in range(3):
   tap(e,4,r=2,c=3);frames=settle(e,2000+m*100+i*14)
   assert all(v<=bound for frame in frames for px in frame for v in px),(cap,m,bound)
 # Clamp an already filled, potentially corrupt maximum buffer at serialization.
 e.u.mem_write(S['pixels'],b'\xff'*1344);e.set('pending',255)
 frames,n=e.frame();assert all(v<=bound for f in frames for px in f for v in px)
 # Blanking precedes ANY serial clock rising edge.
 edges=0;offs=set()
 for a,v in e.w:
  if a in rows and not v:offs.add(a)
  if a==0x50004280 and v:assert len(offs)==7;break
# WDT is never fed solely because main spins; requires scan progress.
e=Device();e.render(1500);e.w=[]
e.render(1501);assert not any(a==0x40004008 for a,v in e.w)
e.frame();e.w=[];e.render(1502);assert (0x40004008,0x5aa5) in e.w
# USB not configured: stay dark, then recover only when configuration returns.
e=Device();e.u.mem_write(0x20007005,b'\x01');e.render(2000);assert not e.get('running')
e.u.mem_write(0x20007005,b'\0');e.render(2001);assert e.get('running')
e.frame();e.u.mem_write(0x20007005,b'\x01');e.frame();assert not any(e.gates.values())
e.render(2002);assert not e.get('running')
assert int.from_bytes(e.u.mem_read(0x400400d8,4),'little')&2==0
assert int.from_bytes(e.u.mem_read(0x40040020,4),'little')&2==0
assert int.from_bytes(e.u.mem_read(0x40004000,4),'little')&0x80==0
# WDT-reset/CPU-lockup boots leave RGB disabled.
for flags in [4,256]:
 e=Device();e.u.mem_write(0x50000004,struct.pack('<I',flags));e.render(1500)
 assert e.get('fault') and not e.get('running') and not any(e.gates.values())
# Invalid scan state and CM nibbles fail bounded, no arbitrary table read.
e=Device();e.render(1500);e.set('active',2);e.frame();assert e.get('fault') and not any(e.gates.values())
e=Device();e.render(1500);e.u.mem_write(S['zones'],b'\xff'*384);e.u.mem_write(S['zone_on'],b'\1\1')
frames=settle(e,2000);assert all(v<=36865 for f in frames[:6] for px in f for v in px)
# Read-only diagnostics; unknown writes remain unhandled.
e.u.mem_write(0x20008100,bytes([8,1,1,0])+bytes(28));e.call('via_custom_value_command_kb',0x20008100,32)
e.u.mem_write(0x20008100,bytes([7,1,1,0])+bytes(28));e.call('via_custom_value_command_kb',0x20008100,32);assert e.u.mem_read(0x20008100,1)==b'\xff'
print(json.dumps({'result':'PASS','checks':['11 original LUT levels with independent 90 percent hard ceiling','independent indicators all states and levels','VIA bounds/get/set/unknown commands','12 modes with min/max speeds and 25% master','Alt indicator controls vs extra master','stock palette and consumed release','CM1/CM2 record/commit/priority/black/timeout','hold off includes zones','suspend and both fault cutoffs'],'additional_checks':['hard ceiling all 12 modes and queued frames','indicators included','red bit-15 encoding never exceeds ceiling','blanking before shift','WDT feed requires main plus scan','USB configuration gating and PWM stop','fail-dark watchdog reboot','CM bounds and diagnostics'], 'hardware_validated':False},indent=2))

# Snapshot roundtrip preserves durable RGB settings and refuses malformed data.
e=Device();e.render(1500)
via(e,2,9);via(e,3,5);via(e,8,6);via(e,12,73);via(e,4,7)
via(e,10,1);via(e,11,1);e.u.mem_write(S['zones']+2*35,struct.pack('<H',0x8aa0))
e.u.mem_write(S['zones']+192+2*35,struct.pack('<H',0x8000));e.u.mem_write(0x20007006,b'\x01')
e.call('ducky_rgb_export',0x20009000)
snapshot=bytes(e.u.mem_read(0x20009000,416))
e.call('ducky_rgb_defaults');assert via(e,2)==0 and via(e,3)==9 and via(e,12)==90
f=Device();f.u.mem_write(0x20009000,snapshot);f.call('ducky_rgb_import',0x20009000)
assert f.u.reg_read(UC_ARM_REG_R0)==1
assert (via(f,2),via(f,3),via(f,8),via(f,12),via(f,4))==(9,5,6,73,7)
f.call('ducky_rgb_export',0x20009200);assert bytes(f.u.mem_read(0x20009200,416))==snapshot
for offset,value in [(0,2),(2,12),(3,11),(7,0),(8,91),(9,4),(10,2),(12,255),(32,255)]:
 bad=bytearray(snapshot);bad[offset]=value;f.u.mem_write(0x20009000,bytes(bad));f.call('ducky_rgb_import',0x20009000)
 assert f.u.reg_read(UC_ARM_REG_R0)==0
 assert via(f,12)==73
print('PASS: RGB persistent snapshot roundtrip, defaults and invalid-field rejection')
