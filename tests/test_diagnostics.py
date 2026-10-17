# SPDX-License-Identifier: GPL-2.0-or-later
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import diagnostics

class FakeDevice:
    def __init__(self, extended=True, truncated=False, version=1):
        self.extended, self.truncated = extended, truncated
        self.version = version
        self.requests = []
    def write(self, request):
        self.requests.append(request)
        assert len(request) == 33 and request[:3] == bytes([0, 8, 1])
        return len(request)
    def read(self, size, timeout):
        request = self.requests[-1][1:]
        reply = bytearray(request)
        index = request[2]
        if index >= 8 and not self.extended:
            reply[0] = 255
        else:
            value = {0:0x6c, 3:4, 7:0x5a01, 8:(self.version<<24)|1, 9:3, 10:500,11:4,12:100,13:2,14:1}.get(index, 0)
            reply[4:8] = value.to_bytes(4, 'little')
        return reply[:4] if self.truncated else reply

class DiagnosticsTests(unittest.TestCase):
    def test_usb_wait_diagnostics(self):
        dev=FakeDevice(version=2)
        result=diagnostics.collect(dev)
        self.assertEqual(result['diagnostics_version'],2)
        self.assertEqual(result['usb_wait_peak_scans'],100)
        self.assertEqual(result['usb_last_event'],1)
        self.assertEqual(len(dev.requests),15)
    def test_extended_shutdown_report(self):
        dev = FakeDevice()
        result = diagnostics.collect(dev)
        self.assertTrue(result['rgb_fault'])
        self.assertFalse(result['rgb_running'])
        self.assertEqual(result['rgb_fault_reason_code'], 1)
        self.assertEqual(result['usb_pause_count'], 3)
        self.assertTrue(result['reset_flags']['watchdog'])
        self.assertTrue(result['reset_flags']['low_voltage'])
        self.assertFalse(result['reset_flags']['brown_out'])
        self.assertEqual(len(dev.requests), 11)
    def test_legacy_firmware(self):
        dev = FakeDevice(extended=False)
        result = diagnostics.collect(dev)
        self.assertEqual(result['diagnostics_version'], 0)
        self.assertNotIn('usb_pause_count', result)
        self.assertEqual(len(dev.requests), 9)
    def test_incomplete_reply_is_not_a_legacy_response(self):
        with self.assertRaises(RuntimeError):
            diagnostics.collect(FakeDevice(truncated=True))
