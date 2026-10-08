# Native for-loop control

Range-loop `continue` used to jump to the header before advancing the hidden
counter. At Clang O0 this could loop forever; at O2 the invalid progress
assumption could produce incorrect output instead. Map loops additionally lacked
their own control targets: top-level `break`/`continue` could do nothing, and a
nested map could jump into its enclosing loop.

`lower_for` and `lower_for_map` now bind the current user-visible value first,
then advance the hidden counter before lowering the user's body. Normal
fallthrough and `continue` both return to the header, with advancement already
complete. The visible value, bounds evaluation and block layout stay the same.
`break` and return may advance an unobservable counter, then leave the loop.
Map lowering saves, installs and restores its own header/exit targets, matching
range and while lowering. No state-layout or runtime change is required.

`tests/integration/test_native_for_continue.py` executes nine programs at Clang
O0 and O2. They cover conditional and unconditional continue, inclusive/negative
bounds, empty/reversed ranges, nested range/map/while loops, break, and early
return. Expected output and a three-second execution timeout detect both
nonprogress and jumps into the wrong loop. The preserved native compiler failed
16 of 18 checks; only the empty-range controls passed. The candidate passes all
18 native checks.

Golden `104_for_continue.mn` and its expected output are required executable
fixtures in `scripts/verify_fixed_point.py`. Both compiler generations must run
it successfully, not merely emit LLVM-valid IR. This raises the strict corpus
to 104 LLVM goldens and nine executable fixtures per generation.

## Bootstrap iterator follow-up

The six bootstrap failures exposed by the native comparison are now fixed.
All 36 native/bootstrap control-flow cases pass at Clang O0/O2, with no expected
failures. The runtime implements `__mn_range_inclusive` using an inclusive flag
and an exhaustion flag, avoiding `end + 1` and signed overflow at `INT64_MAX`.
The public handle remains opaque; existing exclusive-range behavior is preserved.

Python lowering creates a separate map cursor in each loop's preheader. The
header advances that cursor once, and the body loads its typed key. Previously
the header created a fresh cursor on each visit, continually restarting the
map. Map literals also retain their key/value type arguments, so String keys
are loaded as String values rather than raw pointers.

Each cursor has a null-initialized function-entry slot. Normal exit and `break`
free it and clear that slot; function-return cleanup releases any still-active
cursors. Nested and sequential loops over the same map have independent slots.
Cursor creation borrows the map and does not transfer its ownership. This is
private iterator cleanup, not adoption of the owned-container runtime API.

`test_bootstrap_iterators.py` exercises five programs at Python O0–O3 under
ASan/LSan: nested/repeated loops over one map, integer keys, typed empty maps
followed by insertion, conditional early returns through nested loops, and
inclusive iteration ending at `INT64_MAX`. The C range probe checks twelve
exclusive/inclusive boundary cases against both instrumented runtime source and
the optimized archive. These tests pass alongside the existing runtime controls.

The separate map-return use-after-free exposed here is now fixed for direct
Map returns. Callee cleanup preserves the escaping pointer, and callers track
results only from proven factories; borrowed results stay conservative. See
[the return contract](../memory-ownership/MAP_RETURNS.md). Replacing handles in
loops, aggregate returns and general container ownership remain separate work.

Evidence: `build/memory-ownership/range-continue/baseline-tests.log` records
22 failures (16 native and six bootstrap) and 14 passes before the native fix.
`candidate-tests.log` records 30 passes and the same six bootstrap failures before
they were marked. Later verification and promotion are recorded in the
[ownership work log](../memory-ownership/WORK_LOG.md).

Follow-up evidence: `build/memory-ownership/bootstrap-iteration/`. The strict
gate is `build/fixed-point-uvraczp_`: 104 LLVM goldens and nine required outputs
per generation, with byte-identical stage2/stage3 IR.
