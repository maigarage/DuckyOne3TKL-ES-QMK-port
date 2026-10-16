# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed flashing policy. No automatic boot-entry, chip erase or CONFIG write."""
import hashlib
import json
import os
import struct
import time
from pathlib import Path

from target import APP_ID, BOOT_IDS, EXPECTED, ORIGINAL_SHA256, STOCK_NAME


def packet(command, payload=b""):
    if len(payload) > 56:
        raise ValueError("Payload exceeds 56 bytes")
    return struct.pack("<II", command, 0) + payload + bytes(56 - len(payload))


def image_packets(data):
    if not 48 <= len(data) <= 0x1e000:
        raise ValueError("APROM image size must be 48..122880 bytes")
    sp, reset = struct.unpack_from("<II", data)
    if not (0x20000000 < sp <= 0x20005000 and sp % 4 == 0 and
            reset & 1 and 8 <= (reset & ~1) < len(data)):
        raise ValueError("Invalid NUC1261 APROM vector table")
    yield packet(0xA0, struct.pack("<II", 0, len(data)) + data[:48])
    for i in range(48, len(data), 56):
        yield packet(0, data[i:i + 56])


def load_image(path, sha256):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("Firmware SHA-256 mismatch; no programming permitted")
    list(image_packets(data))
    return data


class Transport:
    def __init__(self, device):
        self.device, self.next_reply = device, 2

    def write(self, data):
        if len(data) != 64 or self.device.write(b"\0" + data) != 65:
            raise RuntimeError("Incomplete HID write; command is NOT retried")

    def exchange(self, data, reset_sequence=False):
        if reset_sequence:
            self.next_reply = 2
        self.write(data)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            raw = bytes(self.device.read(64, 1000))
            if not raw:
                continue
            if len(raw) != 64:
                raise RuntimeError("Unexpected HID reply length")
            sequence = struct.unpack_from("<I", raw, 4)[0]
            if sequence != self.next_reply:
                raise RuntimeError("HID reply sequence mismatch; command is NOT retried")
            self.next_reply += 2
            return raw
        raise TimeoutError("No bootloader acknowledgement; command is NOT retried")

    def sync(self):
        self.exchange(packet(0xA4, struct.pack("<I", 1)), True)

    def identify(self):
        self.exchange(packet(0xAE), True)
        self.sync()
        version = self.exchange(packet(0xA6))[8]
        pdid = struct.unpack_from("<I", self.exchange(packet(0xB1)), 8)[0]
        config = struct.unpack_from("<II", self.exchange(packet(0xA2)), 8)
        return dict(pdid=f"0x{pdid:08x}", bootloader_version=version,
                    config0=f"0x{config[0]:08x}", config1=f"0x{config[1]:08x}")


def boot_devices(hid):
    return [d for vid, pid in BOOT_IDS for d in hid.enumerate(vid, pid)
            if (d.get("usage_page"), d.get("usage")) == (1, 0)]


def candidate(info, data):
    for key, value in EXPECTED.items():
        if info.get(key) != value:
            raise ValueError(f"Unsupported {key}: {info.get(key)}; expected {value}. Nothing written.")
    list(image_packets(data))
    if len(data) > int(info["config1"], 16):
        raise ValueError("Image crosses the observed APROM/data-flash boundary")


def application_status(hid):
    """Descriptor evidence only: LDROM cannot read back/identify the previous APROM."""
    devices = hid.enumerate(*APP_ID)
    if any("experimental port" in (d.get("manufacturer_string") or "").lower()
           and (d.get("usage_page"), d.get("usage")) == (0xff60, 0x61) for d in devices):
        return "QMK port detected from USB descriptors (image/version not read back)"
    if any((d.get("usage_page"), d.get("usage")) in ((0xff00, 1), (1, 0)) for d in devices):
        return "Ducky original-compatible USB interface detected (exact image not verified)"
    return "Unknown: disconnected, already in bootloader, or unrecognized application"


def state_directory():
    # Preserve the previous listener's pending marker across package upgrades.
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share")))
    return base / "DuckyOne3TKLFlasher"


class Journal:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else state_directory()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "pending.json"
        self.lock = None

    def acquire(self):
        self.lock = (self.directory / "listener.lock").open("a+b")
        if self.lock.tell() == 0:
            self.lock.write(b"0")
            self.lock.flush()
        self.lock.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            self.lock = None
            raise RuntimeError("Another flashing assistant is running")

    def close(self):
        if self.lock:
            self.lock.close()
            self.lock = None

    def pending(self):
        # Even malformed/truncated old markers require recovery.
        return self.path.exists()

    def begin(self, action, info, sha256):
        value = {"schema": 1, "action": action, "identity": info,
                 "sha256": sha256, "started_utc": time.time()}
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)
        self._sync_directory()

    def complete(self):
        self.path.unlink(missing_ok=True)
        self._sync_directory()

    def _sync_directory(self):
        if os.name != "nt":
            descriptor = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


class Cancelled(Exception):
    pass


def perform(transport, info, data, action, journal, confirm, progress):
    """The only programming entrypoint: validate -> confirm -> durable marker -> write."""
    candidate(info, data)
    if action not in ("install", "restore"):
        raise ValueError("Unknown action")
    sha = hashlib.sha256(data).hexdigest()
    if action == "restore" and sha != ORIGINAL_SHA256:
        raise ValueError("Restore can only write the pinned Ducky original 1.16")
    if journal.pending() and action != "restore":
        raise ValueError("Unfinished transfer detected. Restore the original first.")
    if not confirm(action, info, sha, len(data)):
        raise Cancelled("Cancelled before programming; no APROM write sent")
    journal.begin(action, info, sha)
    packets = list(image_packets(data))
    transport.sync()
    for n, report in enumerate(packets, 1):
        transport.exchange(report)
        if n == 1 or n % 25 == 0 or n == len(packets):
            progress(f"Acknowledged {n}/{len(packets)} packets")
    progress("All packets acknowledged. Flash read-back verification is NOT available.")
    transport.write(packet(0xAB))
    journal.complete()
    progress("Application start request sent. Check keyboard operation and lighting.")


def images(workspace, action):
    workspace = Path(workspace)
    # Fixed paths: no arbitrary filename or original hash supplied by the manifest.
    original = load_image(workspace / "vendor" / STOCK_NAME, ORIGINAL_SHA256)
    if action == "restore":
        return original
    manifest = json.loads((workspace / "firmware" / "manifest.json").read_text(encoding="utf-8"))
    firmware = load_image(workspace / "firmware" / "qmk.bin", manifest["sha256"])
    return firmware
