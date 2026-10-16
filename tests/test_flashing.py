# SPDX-License-Identifier: GPL-2.0-or-later
"""Transport/policy fault injection; this suite never imports or opens real HID devices."""
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import flashing as f
import manage
from target import EXPECTED

IMAGE = struct.pack("<II", 0x20004000, 0x21) + bytes(200)
SHA = hashlib.sha256(IMAGE).hexdigest()


class FakeHIDDevice:
    def __init__(self, failure=None):
        self.writes, self.sequence, self.failure = [], 0, failure

    def write(self, data):
        self.writes.append(bytes(data))
        command = int.from_bytes(data[1:5], "little")
        if command in (0xAE, 0xA4):
            self.sequence = 0
        if self.failure == "short":
            return 64
        if self.failure == "disconnect" and command == 0xA0:
            raise OSError("Cable removed")
        return len(data)

    def read(self, size, timeout):
        self.sequence += 2
        raw = bytearray(64)
        struct.pack_into("<I", raw, 4, self.sequence + (2 if self.failure == "sequence" else 0))
        command = int.from_bytes(self.writes[-1][1:5], "little")
        if command == 0xA6:
            raw[8] = 51
        if command == 0xB1:
            struct.pack_into("<I", raw, 8, 0x01205212)
        if command == 0xA2:
            struct.pack_into("<II", raw, 8, 0xf7ffff7c, 0x00033200)
        return bytes(raw[:-1] if self.failure == "length" else raw)

    def close(self):
        pass

    def open_path(self, path):
        pass

    @property
    def commands(self):
        return [int.from_bytes(w[1:5], "little") for w in self.writes]


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.journal = f.Journal(self.directory.name)
        self.device = FakeHIDDevice()
        self.transport = f.Transport(self.device)

    def perform(self, action="install", confirm=lambda *a: True):
        f.perform(self.transport, dict(EXPECTED), IMAGE, action, self.journal, confirm, lambda s: None)

    def test_probe_has_only_read_identification_and_sync_commands(self):
        self.assertEqual(self.transport.identify(), EXPECTED)
        self.assertEqual(self.device.commands, [0xAE, 0xA4, 0xA6, 0xB1, 0xA2])

    def test_cancel_never_writes(self):
        with self.assertRaises(f.Cancelled):
            self.perform(confirm=lambda *a: False)
        self.assertEqual(self.device.writes, [])
        self.assertFalse(self.journal.pending())

    def test_each_identity_mismatch_blocks_before_confirmation(self):
        for key in EXPECTED:
            info = dict(EXPECTED, **{key: "wrong"})
            with self.assertRaises(ValueError):
                f.perform(self.transport, info, IMAGE, "install", self.journal,
                          lambda *a: self.fail("Must not offer unsupported candidate"), print)
        self.assertEqual(self.device.writes, [])

    def test_bad_vectors_block(self):
        for sp, reset in [(0, 33), (0x20006000, 33), (0x20000001, 33), (0x20004000, 32), (0x20004000, 1001)]:
            with self.assertRaises(ValueError):
                list(f.image_packets(struct.pack("<II", sp, reset) + bytes(200)))

    def test_bad_sizes_block(self):
        for size in (0, 47, 131073):
            with self.assertRaises(ValueError):
                list(f.image_packets(bytes(size)))

    def test_bad_hash_blocks(self):
        path = Path(self.directory.name) / "test.bin"
        path.write_bytes(IMAGE)
        with self.assertRaises(ValueError):
            f.load_image(path, "0" * 64)

    def test_success_only_programs_aprom_and_runs_last(self):
        self.perform()
        self.assertEqual(self.device.commands, [0xA4, 0xA0, 0, 0, 0, 0xAB])
        self.assertFalse(self.journal.pending())

    def test_durable_marker_precedes_first_command(self):
        original = self.device.write
        def write(data):
            self.assertTrue(self.journal.pending())
            self.assertEqual(json.loads(self.journal.path.read_text())["sha256"], SHA)
            return original(data)
        self.device.write = write
        self.perform()

    def test_journal_failure_prevents_all_writes(self):
        with patch.object(self.journal, "begin", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.perform()
        self.assertEqual(self.device.writes, [])

    def test_short_write_retains_marker_and_never_runs(self):
        self.device.failure = "short"
        with self.assertRaises(RuntimeError):
            self.perform()
        self.assertTrue(self.journal.pending())
        self.assertNotIn(0xAB, self.device.commands)
        self.assertEqual(len(self.device.writes), 1)

    def test_disconnect_retains_marker_and_never_runs(self):
        self.device.failure = "disconnect"
        with self.assertRaises(OSError):
            self.perform()
        self.assertTrue(self.journal.pending())
        self.assertNotIn(0xAB, self.device.commands)
        self.assertEqual(self.device.commands.count(0xA0), 1)

    def test_sequence_error_is_not_retried(self):
        self.device.failure = "sequence"
        with self.assertRaises(RuntimeError):
            self.perform()
        self.assertEqual(len(self.device.writes), 1)
        self.assertTrue(self.journal.pending())

    def test_reply_length_error(self):
        self.device.failure = "length"
        with self.assertRaises(RuntimeError):
            self.perform()
        self.assertTrue(self.journal.pending())

    def test_timeout_is_not_retried(self):
        self.device.read = lambda *a: []
        with patch.object(f.time, "monotonic", side_effect=[0, 1, 6]):
            with self.assertRaises(TimeoutError):
                self.perform()
        self.assertEqual(len(self.device.writes), 1)
        self.assertTrue(self.journal.pending())

    def test_malformed_pending_forces_original(self):
        self.journal.path.write_text("{broken")
        with self.assertRaises(ValueError):
            self.perform()
        self.assertEqual(self.device.writes, [])

    def test_restore_rejects_every_nonoriginal_image(self):
        with self.assertRaises(ValueError):
            self.perform("restore")
        self.assertEqual(self.device.writes, [])

    def test_authorized_original_restore_clears_pending(self):
        self.journal.path.write_text("{legacy pending marker}")
        with patch.object(f, "ORIGINAL_SHA256", SHA):
            self.perform("restore")
        self.assertFalse(self.journal.pending())
        self.assertEqual(self.device.commands[-1], 0xAB)

    def test_failed_run_write_keeps_pending(self):
        original = self.device.write
        def write(data):
            if int.from_bytes(data[1:5], "little") == 0xAB:
                raise OSError("Lost connection before run completed")
            return original(data)
        self.device.write = write
        with self.assertRaises(OSError):
            self.perform()
        self.assertTrue(self.journal.pending())

    def test_single_instance_lock(self):
        self.journal.acquire()
        self.addCleanup(self.journal.close)
        other = f.Journal(self.directory.name)
        self.addCleanup(other.close)
        with self.assertRaises(RuntimeError):
            other.acquire()

    def test_multiple_bootloaders_rejected_without_open(self):
        class Hid:
            def enumerate(self, *args):
                return [dict(usage_page=1, usage=0, path=b"one")]
            def device(self):
                raise AssertionError("Must not open ambiguous device")
        assistant = manage.Assistant(Hid(), Path(self.directory.name), self.journal, lambda s: None, lambda *a: True, lambda: False)
        with self.assertRaises(RuntimeError):
            assistant.wait()

    def test_application_detection_does_not_guess_from_bootloader(self):
        class Hid:
            def enumerate(self, *args):
                return []
        self.assertIn("Unknown", f.application_status(Hid()))

    def test_recovery_is_selected_after_failed_install_and_reconfirmed(self):
        first, second = FakeHIDDevice("disconnect"), FakeHIDDevice()
        actions = []
        assistant = manage.Assistant(None, Path(self.directory.name), self.journal, lambda s: None,
                                     lambda action, *a: actions.append(action) or True, lambda: False)
        with patch.object(assistant, "wait", side_effect=[first, second]), patch.object(manage, "images", return_value=IMAGE), \
             patch.object(f, "ORIGINAL_SHA256", SHA), patch.object(manage.time, "sleep"):
            assistant.run("install")
        self.assertEqual(actions, ["install", "restore"])
        self.assertNotIn(0xAB, first.commands)
        self.assertEqual(second.commands[-1], 0xAB)
        self.assertFalse(self.journal.pending())

    def test_cancelling_recovery_preserves_pending(self):
        self.journal.path.write_text("pending")
        with patch.object(f, "ORIGINAL_SHA256", SHA):
            with self.assertRaises(f.Cancelled):
                self.perform("restore", lambda *a: False)
        self.assertTrue(self.journal.pending())
        self.assertEqual(self.device.writes, [])


if __name__ == "__main__":
    unittest.main()
