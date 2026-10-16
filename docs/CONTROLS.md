# VIA, lighting and indicators

Load `via/ducky-one3-tkl-rgb.json` in VIA's Design tab as a v3 definition, then open
Configure → Lighting. This is a custom Ducky lighting menu; it is not the standard
QMK RGB Matrix backend. Close VIA before flashing or reading diagnostics.

The effect sequence is Full Backlit, Wave, Color Cycle, Rain Drop, Ripple, Rainbow
Reactive, Reactive, Halo, Breathe, Radar, Laser and Off. The adapter uses the
identified Ducky 1.16 calculations, per-mode parameters, palette and electrical
to geometric remapping. Matching calculations in emulation does not prove matching
wall-clock timing on the physical keyboard.

The 11 original nonlinear RGB levels are retained. `Master scale (extra)` is an
additional port control that scales key RGB. It starts at level 9 (~56.25%). The
indicators have a separate level. `Global maximum brightness (%)` is a shared
final ceiling, initially 90%, enforced in firmware for every output path. Set it
to 0 to suppress all lighting, including indicators. The full table is in
[SAFETY.md](SAFETY.md).

## Default keyboard shortcuts

`Fn` is the key mapped to momentary layer 1. Remapping that layer in VIA can
change these shortcuts.

| Shortcut | Function |
| --- | --- |
| Fn + F5 / F6 / F7 | Cycle red / green / blue level in color-configurable effects |
| Fn + F8 | Clear the selected color channels |
| Fn + F9 | Toggle the base effect |
| Fn + F10 | Next effect; hold for 3 seconds to turn off effects/zones/palette |
| Fn + Up / Down | Increase / decrease the port's master brightness |
| Fn + Alt + Up / Down | Increase / decrease independent indicator brightness |
| Fn + Right / Left | Change the selected effect's speed parameter |
| Fn + Space | Toggle the keyboard color palette in color-configurable effects |
| Fn + F11 / F12 | Toggle CM1 / CM2 |
| Hold Fn + Print Screen / Pause for 5 seconds | Start recording CM1 / CM2 |

Speed ranges are mode-specific: generally 0–9, Radar 0–10. Some effects ignore
the RGB-channel settings. The VIA definition hides controls where appropriate;
firmware also bounds incoming values.

## CM1 and CM2

These are two custom per-key lighting overlays. They do not correspond to two
fixed physical halves of the keyboard. You choose which keys belong to each
overlay and their colors. CM1 takes priority over CM2; an explicitly painted black
key can override the background with darkness.

During recording, tap keys to paint them. Hold Caps Lock and use F5/F6/F7 to cycle
paint color channels, F8 for black, or Space for palette selection. Caps Lock +
Scroll Lock commits the zone. An inactivity timeout discards an uncommitted draft.
Committing a zone applies it in RAM. Use **Save current settings to flash** to
retain committed zones after power removal; uncommitted drafts are never saved.

## Separate indicators

The three separate indicators are Caps Lock, Scroll Lock and the keyboard's
mouse-function mode indicator. The third indicator is not a general Pause-key
backlight. Keyboard RGB and these indicators use separate controls, then share
the common final brightness ceiling. Indicator brightness starts at level 9 (~56.25%).

Toggle mouse mode with **Fn + Alt + Scroll Lock**. In that mode, Home/End move
up/down, Delete/Page Down move left/right, Insert/Page Up are the left/right mouse
buttons, and Print Screen/Pause scroll down/up. The third indicator tracks this
mode. Releasing keys or suspending USB releases the associated mouse actions.

## Persistence and limitations

Changes take effect in RAM immediately. Test10 adds explicit saving to internal
flash through **Settings storage** in VIA or the **Settings-Ducky** launcher.
Saved settings load at power-up, including keymaps/macros, lighting, the ceiling
and CM zones. Unsaved changes are lost on power removal. See
[PERSISTENCE.md](PERSISTENCE.md) for saving, resetting and failure behavior.
The USB product string identifies `test10`; bcdDevice is `0x0020`.

The vendor [One 3 manual](https://cdn.shopify.com/s/files/1/0728/4382/1295/files/Ducky_One3_usermanual_V15_20250512.pdf?v=1747019443)
is a behavioral reference. This port does not claim to reproduce every commercial
Ducky function, profile, macro or persistent setting described there.
