# Reproducing the analysis

These scripts use the exact hash-pinned Ducky 1.16 input prepared by setup. They
do not open a USB device or write firmware. Run with the runtime Python and pass
the private workspace directory:

```bash
"$work/runtime/bin/python" research/recover_matrix.py "$work"
"$work/runtime/bin/python" research/verify_geometry.py "$work"
"$work/runtime/bin/python" research/verify_bank_gates.py "$work"
```

`recover_matrix.py` evaluates the GPIO initialization block to recover the six
row and sixteen column pins. `verify_geometry.py` executes the original renderer
with unique tagged colors to verify the five exceptional LED geometry mappings.
`verify_bank_gates.py` checks the original seven-bank gate table and on/off writes,
including the bank shared with the independent indicators.

The complete current extraction/relocation pipeline is in
`tools/generate_vendor.py`, not in an omitted notebook or manual patch. It includes
the updater extraction, bounded RAM initialization, literal-pool discovery and
assembly/data generation. The current stock-versus-port comparison is
`tests/firmware/compare_stock_engine.py`, run by `tools/validate.py`.

Old experiments, standalone disassembly dumps, intermediate binaries and obsolete
release scripts have been removed. Generated vendor bytes remain in the private
workspace and must not be committed to this source repository.
