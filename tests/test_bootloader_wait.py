"""Exercise the USB settle gate with a virtual clock; never opens hardware."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import manage


class BootloaderWaitTests(unittest.TestCase):
    def exercise(self, change=None, stop_at=None):
        now = [0.0]
        hid = Mock()
        device = hid.device.return_value
        logs = []
        assistant = manage.Assistant(hid, None, None, logs.append, None,
                                     lambda: stop_at is not None and now[0] >= stop_at)
        def devices(_):
            if change is not None and now[0] >= 2:
                return change
            return [{"path": b"ducky"}]
        def sleep(seconds):
            device.write.assert_not_called()
            now[0] += seconds
        with patch.object(manage.time, "monotonic", side_effect=lambda: now[0]), \
             patch.object(manage.time, "sleep", side_effect=sleep), \
             patch.object(manage, "boot_devices", side_effect=devices):
            if stop_at is not None:
                with self.assertRaises(manage.Cancelled):
                    assistant.wait()
                device.close.assert_called_once()
            elif change is not None:
                with self.assertRaises(RuntimeError):
                    assistant.wait()
                device.close.assert_called_once()
            else:
                self.assertIs(assistant.wait(), device)
                self.assertGreaterEqual(now[0], 10)
                self.assertLess(now[0], 10.01)
                device.close.assert_not_called()
            device.write.assert_not_called()
        return now[0]

    def test_full_wait_without_commands(self):
        self.exercise()

    def test_cancel_during_wait_closes_device(self):
        self.assertLess(self.exercise(stop_at=2), 2.2)

    def test_replaced_device_blocks(self):
        self.exercise(change=[{"path": b"different"}])

    def test_multiple_devices_block(self):
        self.exercise(change=[{"path": b"ducky"}, {"path": b"other"}])

    def test_missing_device_blocks(self):
        self.exercise(change=[])


if __name__ == "__main__":
    unittest.main()
