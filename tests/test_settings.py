# SPDX-License-Identifier: GPL-2.0-or-later
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from settings import Settings

class FakeDevice:
    def __init__(self):
        self.writes=[];self.code=1;self.version=10;self.revision=3;self.closed=False;self.armed=False
    def open_path(self, path): pass
    def close(self): self.closed=True
    def write(self, data):
        self.writes.append(data)
        if data[1]==7 and data[3]==2:self.armed=True
        if data[1]==7 and data[3] in (1,3):self.code=9 if data[3]==3 else 3
        return len(data)
    def read(self, size, timeout):
        data=bytearray(self.writes[-1][1:])
        if data[:3]==bytes([8,2,0]):data[3:8]=bytes([self.code,self.version,self.revision,1,int(self.armed)])
        return data

class FakeHID:
    def __init__(self):self.dev=FakeDevice();self.count=1
    def enumerate(self,*args):return [{'usage_page':0xff60,'usage':0x61,'path':b'fake'}]*self.count
    def device(self):return self.dev

class SettingsTests(unittest.TestCase):
    def test_status_is_read_only(self):
        h=FakeHID();s=Settings(h);self.assertEqual(s.status()['code'],1)
        self.assertTrue(all(p[1]==8 for p in h.dev.writes))
    def test_save_only_explicit_command(self):
        h=FakeHID();s=Settings(h);self.assertEqual(s.apply()['code'],3)
        self.assertEqual([p[3] for p in h.dev.writes if p[1]==7],[1])
    def test_reset_is_one_ram_only_command(self):
        h=FakeHID();s=Settings(h);self.assertEqual(s.apply(True)['code'],9)
        self.assertEqual([p[3] for p in h.dev.writes if p[1]==7],[3])
    def test_older_firmware_refused_before_restore_or_save(self):
        for revision in (1,2):
            h=FakeHID();h.dev.revision=revision
            with self.assertRaises(RuntimeError):Settings(h)
            self.assertTrue(all(p[1]==8 for p in h.dev.writes))

    def test_wrong_version_never_writes(self):
        h=FakeHID();h.dev.version=9
        with self.assertRaises(RuntimeError):Settings(h)
        self.assertTrue(h.dev.closed);self.assertTrue(all(p[1]==8 for p in h.dev.writes))
    def test_multiple_devices_rejected(self):
        h=FakeHID();h.count=2
        with self.assertRaises(RuntimeError):Settings(h)
        self.assertEqual(h.dev.writes,[])
    def test_failure_not_reported_as_success(self):
        h=FakeHID();s=Settings(h)
        def exchange(command,setting,value=0):return bytes([command,2,setting,6,10,3])+bytes(26)
        s.exchange=exchange
        with self.assertRaisesRegex(RuntimeError,'Unknown'):s.apply()

if __name__=='__main__':unittest.main()
