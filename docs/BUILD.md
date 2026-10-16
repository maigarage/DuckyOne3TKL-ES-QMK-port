# Sources and rebuilding

## Source boundary

`source-overlay/` contains every modified project file relative to QMK. Setup
fetches the selected upstream source directories and dependencies, preserves their
copyright/license notices, and overlays these files. Upstream sources are not
duplicated in the small public ZIP.

| Repository | Pinned revision |
| --- | --- |
| [qmk/qmk_firmware](https://github.com/qmk/qmk_firmware) | `7a1bbf37c5c07da4ea0a162bb139083a46ef40a1` |
| [qmk/ChibiOS](https://github.com/qmk/ChibiOS) | `6170ddf92d55be54c89b708d1882eea229edeb2c` |
| [qmk/ChibiOS-Contrib](https://github.com/qmk/ChibiOS-Contrib) | `5a9ad82b6ba4f649cdb800e8c2bbc9be2d3ce767` |
| [qmk/lufa](https://github.com/qmk/lufa) | `549b97320d515bfca2f95c145a67bd13be968faa` |
| [qmk/printf](https://github.com/qmk/printf) | `c2e3b4e10d281e7f0f694d3ecbd9f320977288cc` |

The dependency pins come from the QMK parent commit's gitlinks. Each dependency is
checked out independently at that exact revision. Their source files and license
texts remain in the checkout, rather than being replaced by a blanket project
license. This ARM board uses ChibiOS USB, but also needs shared LUFA USB descriptor
headers. Those headers are retained; LUFA demos and board examples are excluded.

New checkouts use Git `--depth 1 --filter=blob:none` with sparse checkout configured
**before checkout**. This avoids downloading the contents of other keyboards,
documentation, demos and unrelated MCU SDKs. The precise directory allowlists are
in `tools/sources.py`; root license files and ancestor-level files are retained
by Git's cone-mode rules. Repository tree/index metadata is still needed. This is
a reduced build checkout, not a claim that every included header is used by the
compiler. Git documentation: [partial clone](https://git-scm.com/docs/git-clone)
and [sparse checkout](https://git-scm.com/docs/git-sparse-checkout).

Existing verified checkouts are reused without deleting local edits or converting
a complete tree to sparse. QMK MSYS remains the Windows toolchain distribution:
reducing the source checkout does not remove the compiler and its runtime tools.

QMK CLI is pinned to 1.2.0 for Linux builds. Host flashing/analysis dependencies
are pinned in `requirements.txt`. QMK's transitive Python packages, OS packages
and reused system toolchains are not fully locked. Setup records package versions
and compiler/dependency provenance. Source rebuilding is supported; identical
binary hashes across all toolchain versions and dates are not promised. QMK embeds
the build date in VIA's RAM EEPROM initialization magic. In the release check,
the earlier source-cleanup baseline differed by only two date-derived bytes from test9 with the same
GCC 13.2.1 toolchain; no lighting/MCU logic was changed by packaging.

## Private vendor inputs

`tools/prepare.py WORKSPACE` downloads the official TKL RGB 1.16 updater over
HTTPS, verifies its full hash, and invokes `generate_vendor.py`. A changed download
is rejected rather than silently treated as compatible.

| Input | SHA-256 |
| --- | --- |
| Official updater | `ae0c326633dc2d81379d132f48cff54a0152331cf14c3aa3d3594cc46e3903d5` |
| Original APROM, 43746 bytes | `e04458f82c1a14baa1b77fd4d63c1b9046a93fd2ed6efe5fc778fbbf87d72c59` |

The original image is extracted at updater offset `0x1a9f70`. The extractor never
runs the EXE. Unicorn executes bounded initialization routines in emulated memory;
Capstone identifies literal pools; the generator emits 68 reviewed RAM-pointer
relocations into the isolated RGB code ranges. A vendor hardware entrypoint at
`0x48ec` is replaced with a return. The generator rejects unexpected inputs or
relocation counts. This is relocated machine code, **not recovered vendor C source**.
The engine is native code within the firmware, not a hardware-isolated sandbox.

## Linux rebuild after setup

Set the two paths to your source and workspace:

```bash
project=/path/to/ducky-one3-tkl-qmk
work=/home/alex/DuckyOne3
"$work/runtime/bin/python" "$project/tools/prepare.py" "$work"
PATH="$work/build-env/bin:$PATH" "$work/build-env/bin/python" "$project/tools/build.py" "$work"
"$work/runtime/bin/python" "$project/tools/finalize.py" "$work"
```

`build.py` refuses a QMK checkout at a different commit. It only overwrites files
covered by the overlay and regenerates build outputs in its dedicated checkout.
Do not use this workspace as an unrelated development checkout. The explicit
developer `--source PATH` option uses an existing prepared QMK tree and skips
dependency download; it still requires the pinned QMK commit.

For another Linux distribution, install Git, GNU make, Arm GNU bare-metal GCC and
newlib, native GCC, Python 3.12 or newer with venv and Tk, HIDAPI, libusb and libudev
development packages. Create separate runtime and QMK environments as in
`setup-linux.sh`, install its udev rule, then execute the commands above. Automated
package installation on other distributions is not included.

## Windows rebuild

Rerunning `Setup-Windows.cmd` with the same workspace rebuilds the existing pinned
tree and validates the output. The existing QMK MSYS installation is reused so the
installer cannot silently uninstall an unrelated version. A new QMK MSYS 1.12.0
installation and Python 3.12.10 installer are verified by pinned SHA-256 values.
Their unattended flags handle installer pages/licenses; Windows UAC remains an
operating-system requirement.

For manual rebuilding, `scripts/build-msys.sh` runs inside QMK MSYS with
`DUCKY_PROJECT` and `DUCKY_WORKSPACE` set to Windows paths. Extraction/finalization
and flashing use the isolated native Python environment. Keeping the environments
separate avoids the conflicting `hid` modules used by QMK and cython-hidapi.

The Windows launcher passes the shell script filename directly to `bash --login`.
It does not pass a quoted shell expression through `bash -c`, which failed with
Windows PowerShell 5.1's native argument handling in the original source package.
`tests/test_windows_launch.ps1` exercises this boundary with a script path
containing spaces and parentheses. Both platforms save compiler output to
`WORKSPACE/build.log` and preserve a failing exit code.

## Build artifacts and tests

Local-only outputs are `WORKSPACE/firmware/qmk.bin`, `qmk.elf`, `qmk.map`,
`build-provenance.json` and `manifest.json`. Finalization validates vectors, RAM,
required handlers, descriptor identity, the ELF/BIN correspondence and original
recovery image before creating a manifest accepted by the assistant.

Host tests need only Python and never open a USB device:

```bash
python3 -m unittest discover -s tests -v
```

The full emulation suite requires the runtime dependencies, Arm compiler/tools
and a native C compiler in PATH. On Linux after setup:

```bash
"$work/runtime/bin/python" "$project/tools/validate.py" "$work"
```

It stages private fixtures under `WORKSPACE/validation-run`, compiles an ARM
harness, checks all 12 effects and brightness clamps, runs linked safety checks,
compares the 11 brightness codes with stock initialization, compares 480 stock
engine updates, and runs the mouse state-machine test. It can take several
minutes. Setup runs the fast host suite and linked-image structural validation;
the longer emulation suite is a separate developer check.

Read-only register diagnostics, with QMK running and VIA closed:

```bash
"$work/runtime/bin/python" "$project/tools/diagnostics.py"
```

On Windows use `WORKSPACE\runtime\Scripts\python.exe` for the host tests and
diagnostics. The cross-platform host suite does not verify Windows USB behavior.

## Create a clean public ZIP

```bash
python3 tools/package.py /path/outside/the/repository/Ducky-One3-TKL-QMK-Source.zip
```

The packager allows only source/documentation directories and refuses compiled
firmware, vendor blobs and executables. It excludes caches, downloads,
build outputs and the entire working directory. Do not upload your workspace.

## Test10.2 persistence

The upstream QMK and HAL pins remain those of the VIA/test9 baseline. The custom
EEPROM backend keeps a 2048-byte live RAM cache. Only explicit Save persists it.
Restore defaults only changes RAM. See PERSISTENCE.md.
The linker reserves the final 8 KiB of the conservative 128 KiB application window;
`finalize.py` rejects overlapping images and requires the FMC routine in SRAM.
The public archive remains source-only; the generated Ducky-derived inputs and
compiled firmware stay in the local workspace. `Settings-Ducky` launchers are
created alongside `Manage-Ducky` after setup.

Run the storage fault-injection test on Linux:

```bash
cc -std=c11 -Wall -Wextra -Werror -O2 \
  -Isource-overlay/keyboards/ducky/one3/tkl_rgb_experimental \
  tests/storage/test_store.c \
  source-overlay/keyboards/ducky/one3/tkl_rgb_experimental/ducky_store.c \
  -o /tmp/ducky-store-test
/tmp/ducky-store-test
```

The Linux persistence-controller harness is included in `tools/validate.py` and CI.
It compiles the actual controller and dual-bank store against fake flash/MMIO and
exercises manual-only writes, legacy auto flags/commands, RAM-only defaults,
key/USB/CM gates, failures, deduplication and snapshot compatibility.
The linked ARM `test_linked_settings.py` checks the real compiled command handler.
