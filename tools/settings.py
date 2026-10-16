#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Save test10.3 settings to flash or restore port defaults in RAM."""
import argparse
import json
import time

STATUS = ['Defaults (not saved)', 'Loaded from flash', 'Waiting for all keys to be released',
          'Saved and verified', 'Already saved; no flash write needed',
          'Write failed; previous valid snapshot retained',
          'Unknown or incomplete flash contents: nothing erased', 'Target mismatch: storage blocked',
          'Legacy reset status', 'Defaults restored in RAM; click Save to keep them after unplugging']


class Settings:
    def __init__(self, backend):
        devices = [d for d in backend.enumerate(0x3233, 0x8311)
                   if d.get('usage_page') == 0xff60 and d.get('usage') == 0x61]
        if len(devices) != 1:
            raise RuntimeError('Expected one Ducky application interface. Close VIA and keep the keyboard in normal mode.')
        self.device = backend.device()
        try:
            self.device.open_path(devices[0]['path'])
            self.status()
        except Exception:
            self.device.close()
            raise

    def close(self):
        self.device.close()

    def exchange(self, command, setting, value=0):
        request = bytes([command, 2, setting, value]) + bytes(28)
        if self.device.write(b'\0' + request) != 33:
            raise RuntimeError('Incomplete HID write')
        reply = bytes(self.device.read(32, 10000))
        if len(reply) != 32 or reply[:3] != request[:3]:
            raise RuntimeError('Incompatible firmware or interface busy. Test10.2 or later is required; close VIA.')
        return reply

    def status(self):
        reply = self.exchange(8, 0)
        if reply[4] != 10 or reply[5] != 3 or reply[3] >= len(STATUS):
            raise RuntimeError('Unexpected settings protocol; no write requested')
        return {'code': reply[3], 'status': STATUS[reply[3]],
                'valid_snapshot': bool(reply[6]), 'reset_armed': bool(reply[7]),
                'protocol_revision': reply[5],
                'auto_save': bool(reply[8]) if reply[5] >= 2 else False,
                'pending_changes': bool(reply[9]) if reply[5] >= 2 else None,
                'manual_save_only': True}

    def apply(self, reset=False):
        self.status()  # Refuse older firmware, whose Restore also writes flash.
        self.exchange(7, 3 if reset else 1, 1)
        until = time.monotonic() + 15
        while time.monotonic() < until:
            state = self.status()
            if state['code'] != 2:
                if state['code'] not in ((9,) if reset else (3, 4)):
                    raise RuntimeError(state['status'])
                return state
            time.sleep(0.15)
        raise TimeoutError('Still waiting: release every key. Request may complete after this window; read status before retrying.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--status', action='store_true')
    group.add_argument('--save', action='store_true')
    group.add_argument('--reset', action='store_true')
    args = parser.parse_args()
    import hid
    if args.status or args.save or args.reset:
        client = Settings(hid)
        try:
            if args.status:
                result = client.status()
            else:
                action = 'restore DEFAULTS in RAM (does not write flash)' if args.reset else 'save ALL current settings to keyboard flash'
                if input(f'Confirm {action}? [y/N] ').strip().lower() != 'y':
                    return
                result = client.apply(args.reset)
            print(json.dumps(result, indent=2))
        finally:
            client.close()
        return
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading
    root = tk.Tk()
    root.title('Ducky test10.3 — Manual settings')
    root.geometry('700x310')
    ttk.Label(root, text='Keep the keyboard connected normally. Do NOT hold D + L.\nClose VIA before using this window.\n\nSave includes all layers, macros, RGB settings and CM1/CM2.\nOnly Save writes flash. Restore defaults changes RAM only.\nFinish CM editing and release every key. RGB briefly turns off when saving.', padding=14).pack(anchor='w')
    state = tk.StringVar(value='Reading keyboard status…')
    ttk.Label(root, textvariable=state, wraplength=590, padding=14).pack(fill='x')
    bar = ttk.Frame(root, padding=12);bar.pack(fill='x')
    buttons = []
    def perform(action):
        if action and not messagebox.askyesno('Confirm settings operation',
                'Restore port defaults in RAM? This replaces current keymaps, macros, RGB and zones. Flash remains unchanged until you click Save.' if action == 'reset' else 'Save ALL current settings to keyboard flash? Keep USB connected until verified.'):
            return
        for button in buttons:button.configure(state='disabled')
        state.set('Working… Release all keys and keep USB connected.')
        def worker():
            client = None
            result = None
            try:
                client = Settings(hid)
                result = client.status() if not action else client.apply(action == 'reset')
                text = result['status']
                if result['pending_changes']:
                    text += '. Current changes are in RAM only.'
                if action == 'reset':
                    text += '. Reopen VIA to refresh its display.'
            except Exception as exc:text = str(exc)
            finally:
                if client:client.close()
            def finish():
                state.set(text)
                for button in buttons: button.configure(state='normal')
            root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()
    for label, action in [('Save current settings to flash', 'save'), ('Restore defaults (RAM only)', 'reset')]:
        button = ttk.Button(bar, text=label, command=lambda a=action:perform(a))
        button.pack(side='left', padx=5);buttons.append(button)
    root.after(0, lambda: perform(None))
    root.mainloop()


if __name__ == '__main__':
    main()
