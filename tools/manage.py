#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Mouse-operated install/restore assistant; CLI fallback uses the same write gate."""
import argparse
import json
import queue
import threading
import time
from pathlib import Path

from flashing import (Cancelled, Journal, Transport, application_status, boot_devices,
                      candidate, images, perform)

BOOTLOADER_SETTLE_SECONDS = 10

INTRO = ("Unplug the Ducky keyboard, then hold D + L while reconnecting it.\n"
         "Release the keys after the bootloader is detected.\n"
         "Close VIA, Ducky's updater and other flashing tools.\n"
         "Choose Install QMK or Restore Ducky original. No firmware is written until you confirm.")


def confirmation(action, info, sha, size):
    return (f"Action: {'INSTALL EXPERIMENTAL QMK' if action == 'install' else 'RESTORE DUCKY ORIGINAL 1.16'}\n\n"
            "The bootloader matches the tested NUC1261 configuration.\n"
            "This identifies the MCU/configuration, not the keyboard PCB.\n"
            "Confirm the label is One 3 TKL RGB, DKON2187ST, and this is the intended keyboard.\n\n"
            f"{json.dumps(info, indent=2)}\nImage: {size} bytes\nSHA-256: {sha}\n\n"
            "Writes APROM only; LDROM and CONFIG are not changed.\n"
            "No flash read-back verification is available.\n"
            "If interrupted, the assistant will offer original-firmware recovery.\n"
            "Do not disconnect while writing. Continue?")


class Assistant:
    def __init__(self, hid, workspace, journal, log, confirm, stopped):
        self.hid, self.workspace, self.journal = hid, workspace, journal
        self.log, self.confirm, self.stopped = log, confirm, stopped

    def settle_bootloader(self, path):
        """Wait before any HID command; abort on cancellation or USB changes."""
        deadline = time.monotonic() + BOOTLOADER_SETTLE_SECONDS
        self.log(f"Bootloader detected. Release D + L. Waiting {BOOTLOADER_SETTLE_SECONDS} seconds before continuing...")
        last_second = None
        while True:
            if self.stopped():
                raise Cancelled("Cancelled during bootloader wait; no programming started")
            devices = boot_devices(self.hid)
            if len(devices) != 1 or devices[0]["path"] != path:
                raise RuntimeError("Bootloader disconnected or device selection changed during the safety wait. Nothing written in this attempt.")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            seconds = int(remaining) + (remaining % 1 > 0)
            if seconds != last_second:
                self.log(f"Bootloader safety wait: {seconds} seconds remaining.")
                last_second = seconds
            time.sleep(min(0.1, remaining))

    def wait(self):
        deadline = time.monotonic() + 180
        self.log("Waiting for bootloader (up to 180 seconds)...")
        while not self.stopped():
            devices = boot_devices(self.hid)
            if len(devices) > 1:
                raise RuntimeError("Multiple matching bootloaders found. Disconnect all except the intended Ducky.")
            if devices:
                dev = self.hid.device()
                try:
                    dev.open_path(devices[0]["path"])
                    self.settle_bootloader(devices[0]["path"])
                except Exception:
                    dev.close()
                    raise
                return dev
            if time.monotonic() >= deadline:
                raise TimeoutError("Bootloader not found. Reconnect holding D + L and try again.")
            time.sleep(0.25)
        raise Cancelled("Cancelled while waiting; no programming started")

    def run(self, action):
        recovering = self.journal.pending()
        if recovering:
            action = "restore"
            self.log("Unfinished transfer marker found: restoration to Ducky original is required.")
        # Three complete attempts, each re-probed and individually confirmed.
        for attempt in range(3):
            device = None
            try:
                data = images(self.workspace, action)
                device = self.wait()
                transport = Transport(device)
                info = transport.identify()
                candidate(info, data)
                self.log("Candidate validated. Waiting for your explicit confirmation.")
                if self.stopped():
                    raise Cancelled("Cancelled before programming")
                perform(transport, info, data, action, self.journal, self.confirm, self.log)
                if action == "restore":
                    self.log("Original restoration acknowledged. Restart the assistant for a new QMK installation.")
                return
            except Cancelled:
                raise
            except Exception as error:
                self.log(f"ERROR: {error}")
                if not self.journal.pending() or attempt == 2 or self.stopped():
                    raise
                action = "restore"
                self.log("Transfer may be incomplete. RUN_APROM will not be sent for an incomplete transfer.\n"
                         "Original recovery is now selected automatically. Keep the keyboard connected.\n"
                         "If USB disappears, reconnect holding D + L. The next candidate still requires confirmation.")
                time.sleep(0.5)
            finally:
                if device:
                    device.close()


def gui(hid, workspace, journal):
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk
    root = tk.Tk()
    root.title("Ducky One 3 TKL RGB — Install / Restore")
    root.geometry("820x620")
    root.minsize(700, 500)
    events = queue.Queue()
    stop = threading.Event()
    busy = [False]
    ttk.Label(root, text=INTRO, wraplength=780, justify="left", padding=12).pack(anchor="w")
    status = tk.StringVar(value="Inspecting currently connected application...")
    ttk.Label(root, textvariable=status, wraplength=780, padding=12).pack(anchor="w")
    recovery = ttk.Label(root, text="", wraplength=780, padding=12)
    recovery.pack(anchor="w")
    bar = ttk.Frame(root, padding=12)
    bar.pack(fill="x")
    log = scrolledtext.ScrolledText(root, state="disabled", wrap="word", height=16)
    log.pack(fill="both", expand=True, padx=12, pady=12)

    def add(text):
        log.configure(state="normal")
        log.insert("end", text + "\n")
        log.see("end")
        log.configure(state="disabled")

    def confirm(*args):
        ready, answer = threading.Event(), []
        events.put(("confirm", (args, ready, answer)))
        ready.wait()
        return answer[0]

    def start(action):
        if busy[0]:
            return
        stop.clear()
        busy[0] = True
        install.configure(state="disabled")
        restore.configure(state="disabled")
        refresh.configure(state="disabled")

        def worker():
            try:
                Assistant(hid, workspace, journal, lambda s: events.put(("log", s)), confirm, stop.is_set).run(action)
            except Exception as e:
                events.put(("log", str(e)))
            finally:
                events.put(("done", None))
        threading.Thread(target=worker, daemon=False).start()

    def detect():
        try:
            status.set("Application observed before bootloader entry: " + application_status(hid))
        except Exception as error:
            status.set("Application unknown: " + str(error))

    install = ttk.Button(bar, text="Install QMK", command=lambda: start("install"))
    install.pack(side="left", padx=4)
    restore = ttk.Button(bar, text="Restore Ducky original", command=lambda: start("restore"))
    restore.pack(side="left", padx=4)
    refresh = ttk.Button(bar, text="Refresh application detection", command=detect)
    refresh.pack(side="left", padx=4)

    def update_buttons():
        pending = journal.pending()
        recovery.configure(text="Unfinished transfer detected. Only restoration to Ducky original is available." if pending else "")
        install.configure(state="disabled" if pending else "normal")
        restore.configure(state="normal")
        refresh.configure(state="normal")

    def close():
        if busy[0]:
            messagebox.showinfo("Operation in progress", "Wait for the operation to finish. Decline the confirmation dialog to cancel before writing.", parent=root)
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)

    def poll():
        try:
            while True:
                kind, value = events.get_nowait()
                if kind == "log":
                    add(value)
                elif kind == "confirm":
                    args, ready, answer = value
                    answer.append(messagebox.askyesno("Confirm target and APROM write", confirmation(*args), default="no", parent=root))
                    ready.set()
                elif kind == "done":
                    busy[0] = False
                    update_buttons()
        except queue.Empty:
            pass
        root.after(100, poll)

    ttk.Button(bar, text="Cancel waiting", command=stop.set).pack(side="right")
    detect()
    update_buttons()
    poll()
    root.mainloop()


def cli(hid, workspace, journal):
    print(INTRO)
    print("Application:", application_status(hid))
    print("CLI requires another keyboard while the Ducky is in bootloader.")
    if journal.pending():
        print("Unfinished transfer found. Only original restoration is available.")
        action = "restore"
    else:
        choice = input("1 = Install QMK, 2 = Restore Ducky original, anything else = Cancel: ").strip()
        if choice not in ("1", "2"):
            return
        action = "install" if choice == "1" else "restore"

    def confirm(*args):
        print(confirmation(*args))
        return input("Type FLASH to confirm the target and start: ").strip() == "FLASH"
    Assistant(hid, workspace, journal, print, confirm, lambda: False).run(action)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--cli", action="store_true")
    args = parser.parse_args()
    import hid
    if not hasattr(hid, "device"):
        raise RuntimeError("Wrong HID binding. Use the launcher created by setup (its isolated hidapi environment).")
    journal = Journal()
    journal.acquire()
    try:
        (cli if args.cli else gui)(hid, args.workspace.resolve(), journal)
    finally:
        journal.close()


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print(f"Stopped: {error}\nIf interrupted during writing, reopen the assistant to restore the original.")
        raise SystemExit(1)
