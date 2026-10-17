# Third-party code, tools and provenance

The root license applies to the project's original GPL-2.0-or-later contributions;
it does not replace the licenses of upstream files, tools, vendor firmware or
trademarks. Existing source copyright headers are preserved. This package does
not bundle installers, compilers, dependency wheels, the original firmware or a
combined firmware binary.

## Included source derived from upstream

| Included files | Upstream and authors | License / notices |
| --- | --- | --- |
| `source-overlay/lib/chibios-contrib/os/hal/ports/NUMICRO/NUC1261/{hal_pal_lld.c,hal_lld.h,nuc123_isr.h,nuc123_registry.h}` | [QMK ChibiOS-Contrib NUMICRO port](https://github.com/qmk/ChibiOS-Contrib); /u/KeepItUnder (2019), Alex Lewontin (2020), as attributed per file | Apache-2.0; original headers retained, text in `licenses/Apache-2.0.txt` |
| `source-overlay/lib/chibios-contrib/os/hal/ports/NUMICRO/LLD/USBv1/hal_usb_lld.c` | Same repository; Alex Lewontin (2020), Ein Terakawa (2021) | Apache-2.0; scoped NUC1261 changes marked |
| `source-overlay/lib/chibios-contrib/os/common/startup/ARMCMx/compilers/GCC/ld/NUC1261_test.ld` | Same repository; Alex Lewontin (2020) | Apache-2.0; adapted linker layout |
| `source-overlay/tmk_core/protocol/chibios/usb_driver.c` | QMK; Stefan Kerkmann, Purdea Andrei, Michael Stapelberg, Ryan (@fauxpark), Fredizzimo, Giovanni Di Sirio | GPL-3.0-or-later OR Apache-2.0; original header retained; finite-send guard added |
| Keyboard `chconf.h` | [QMK firmware](https://github.com/qmk/qmk_firmware), Copyright 2020 QMK | GPL-2.0-or-later; original header retained |

The other project-specific keyboard/board files, NUC1261 clock/SysTick glue,
host tools, research and tests are original project code under GPL-2.0-or-later,
except where a file explicitly carries another inherited notice. See `NOTICE`.
Pinning and source retrieval are documented in [BUILD.md](docs/BUILD.md).

## Upstream sources fetched for building

| Component / repository | Copyright and licensing reference |
| --- | --- |
| [QMK firmware](https://github.com/qmk/qmk_firmware) | QMK/TMK and individual contributors; principally GPL-2.0-or-later, with per-file third-party notices. Preserve the full checkout's licenses. |
| [ChibiOS](https://github.com/qmk/ChibiOS) | Giovanni Di Sirio and other ChibiOS contributors; GPLv3 and component-specific exceptions/alternative licenses. Consult `license.txt`, `readme.txt` and individual source headers. |
| [ChibiOS-Contrib](https://github.com/qmk/ChibiOS-Contrib) | Individual contributors; included NUMICRO files are Apache-2.0. Other subtrees retain their own notices. |
| [LUFA](https://github.com/qmk/lufa) | Dean Camera and contributors; principally MIT, with per-file notices. Initialized dependency, not the selected ARM USB stack. |
| [printf](https://github.com/qmk/printf) | Marco Paland (2014), Eyal Rozenberg (2021); MIT. |
| [Nuvoton NUC1261 BSP](https://github.com/OpenNuvoton/NUC1261BSP) | Nuvoton Technology Corp.; referenced NUC1261 headers/drivers carry Apache-2.0. Used as register/protocol references, not copied wholesale into this ZIP. |
| [Nuvoton ISPTool](https://github.com/OpenNuvoton/ISPTool) | Nuvoton Technology Corp.; protocol reference only. No ISPTool executable/source is redistributed here; consult its repository for applicable terms. |
| Nuvoton NUC123 CMSIS view within ChibiOS-Contrib | Nuvoton Technology Corp. (2014–2016), Apache-2.0 in `NUC123.h`; upstream ARM CMSIS files retain ARM's own notices/licenses. Reused only for compatible register/startup definitions. |

GPL-2.0-or-later does not mean every dependency is GPLv2-only. Where combined
open-source components require GPLv3, use the compatible later GPL version and
preserve the Apache/other notices and exceptions. This does not solve the separate
rights issue for Ducky's proprietary RGB machine code.

## Host tools installed locally

| Tool | Version/source used | Copyright / license reference |
| --- | --- | --- |
| Python | [CPython](https://github.com/python/cpython), Windows installer 3.12.10; Linux distribution package | Python Software Foundation and historical contributors; [PSF license and bundled notices](https://docs.python.org/3/license.html). |
| Tcl/Tk | Python Windows installer / Linux `python3-tk` | Tcl/Tk contributors; permissive Tcl/Tk licenses, [Tcl source](https://github.com/tcltk/tcl) and [Tk source](https://github.com/tcltk/tk). |
| QMK MSYS | [qmk/qmk_distro_msys](https://github.com/qmk/qmk_distro_msys), new installs 1.12.0 | QMK contributors; distribution scripts GPL-3.0. Bundled packages retain separate licenses. |
| MSYS2 | [MSYS2](https://www.msys2.org/), through QMK MSYS | MSYS2/Cygwin and package contributors; package-specific licenses and source links in [MSYS2 packages](https://packages.msys2.org/). |
| Git | [git/git](https://github.com/git/git) | Git contributors; GPL-2.0 with per-file notices. |
| GNU make | [GNU make](https://www.gnu.org/software/make/) | Free Software Foundation and contributors; GPL-3.0-or-later for current versions. |
| Arm GNU compiler/binutils | [GCC](https://gcc.gnu.org/), [Binutils](https://www.gnu.org/software/binutils/); OS or QMK MSYS package | Free Software Foundation and contributors; GPLv3-family licenses, with the GCC Runtime Library Exception where applicable. |
| newlib | [sourceware newlib](https://sourceware.org/newlib/) | Multiple copyright holders and permissive per-file licenses; [license collection](https://sourceware.org/newlib/COPYING.NEWLIB). |
| QMK CLI | [qmk/qmk_cli](https://github.com/qmk/qmk_cli), 1.2.0 on Linux | QMK contributors; MIT (`licenses/QMK-CLI-LICENSE.txt`). |
| pip / setuptools | [pypa/pip](https://github.com/pypa/pip), [pypa/setuptools](https://github.com/pypa/setuptools) | PyPA and contributors; MIT, with vendored dependencies retaining separate notices. |
| cython-hidapi | [trezor/cython-hidapi](https://github.com/trezor/cython-hidapi), 0.14.0.post4 | Pavol Rusnak, TREZOR and contributors; BSD-style, GPLv3 or original license choice. Full license texts are in `licenses/HIDAPI-*`. |
| HIDAPI | [libusb/hidapi](https://github.com/libusb/hidapi) | Alan Ott, Signal 11 Software and contributors; BSD-style/GPLv3/original licensing alternatives; preserve the package's exact notices. |
| libusb | [libusb/libusb](https://github.com/libusb/libusb) | libusb contributors; LGPL-2.1-or-later. |
| libudev / udev | [systemd/systemd](https://github.com/systemd/systemd) or distribution's implementation | systemd/udev contributors; LGPL-2.1-or-later for relevant library code, with per-file notices. |
| Capstone | [capstone-engine/capstone](https://github.com/capstone-engine/capstone), 5.0.3 | Nguyen Anh Quynh and contributors; BSD license plus included LLVM-derived notices (`licenses/Capstone-LICENSE.txt`). |
| Unicorn | [unicorn-engine/unicorn](https://github.com/unicorn-engine/unicorn), 2.1.4 | Nguyen Anh Quynh and contributors, QEMU-derived components; GPLv2 and component-specific notices. [COPYING](https://github.com/unicorn-engine/unicorn/blob/2.1.4/COPYING). |
| pyelftools | [eliben/pyelftools](https://github.com/eliben/pyelftools), 0.32 | Eli Bendersky and contributors; public-domain/Unlicense dedication, with bundled construct license separately noted (`licenses/pyelftools-LICENSE.txt`). |
| VIA application | [the-via/app](https://github.com/the-via/app), external browser application | VIA contributors; GPL-3.0 in the application repository. Not installed or redistributed by this package. [VIA documentation](https://caniusevia.com/docs/). |
| PowerShell | Windows built-in PowerShell 5.1, or [PowerShell 7](https://github.com/PowerShell/PowerShell) | Microsoft and contributors; PowerShell 7 is MIT. Windows PowerShell 5.1 is a Windows component under its applicable Windows terms. |
| GitHub Actions | [actions/checkout](https://github.com/actions/checkout), [actions/setup-python](https://github.com/actions/setup-python) | GitHub and contributors; MIT. Used only by the optional repository CI workflow. |

Runtime Python packages and their transitive metadata/licenses are inventoried
locally by `tools/license_inventory.py`. QMK build dependencies remain in their
own environment and retain their installed license metadata; `pip freeze` records
their versions. System/QMK MSYS packages retain their package-manager copyright
and license records. This ZIP does not redistribute those installed environments.

Setup uses normal unattended installer/package-manager flags and does not alter
license text, fabricate vendor permissions or suppress operating-system
authentication. Running setup requests these local dependency installations.

## Ducky firmware, manual and publication boundary

Original vendor material belongs to DuckyChannel International Co., Ltd. and its
licensors. The [official downloads page](https://ducky.global/pages/downloads)
identifies One 3 TKL RGB as DKON2187ST and links the updater and manual:

- [TKL RGB 1.16 updater](https://cdn.shopify.com/s/files/1/0728/4382/1295/files/Ducky_One_3_TKL_RGB_V1.16.exe?v=1780890244)
- [One 3 manual, V15](https://cdn.shopify.com/s/files/1/0728/4382/1295/files/Ducky_One3_usermanual_V15_20250512.pdf?v=1747019443)

The public availability of those downloads is not an open-source or redistribution
license. The updater, original APROM, extracted RGB machine code, initialization
bytes and combined firmware are excluded from the public source ZIP. The manual
is linked rather than bundled. Neither Ducky's C source nor permission to publish
the combined firmware is available in this project.

The generator's GPL license applies to the generator, not to the vendor bytes it
emits. Before distributing any combined binary, resolve the vendor rights and
corresponding-source obligations, or replace the vendor implementation. Merely
renaming machine code to a `.S` file does not make it original GPL source.

## Test10 reference material

The new storage implementation is project code under GPL-2.0-or-later. Hardware
register constants/protocol behavior were checked against the Apache-2.0
[OpenNuvoton NUC1261BSP](https://github.com/OpenNuvoton/NUC1261BSP), Copyright
Nuvoton Technology Corp. No additional Nuvoton driver source is bundled by test10.
VIA button/label behavior was checked against [the-via/app](https://github.com/the-via/app).
No Vial code or dependency is included in this VIA/QMK release.
