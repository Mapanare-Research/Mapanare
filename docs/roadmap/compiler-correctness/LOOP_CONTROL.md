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

## Remaining bootstrap discrepancies

The Python compiler is unchanged by this native fix. Comparison tests exposed
two existing problems, reproduced against the starting compiler:

- The inclusive range in the new golden emits an unresolved
  `__mn_range_inclusive` reference. Both optimization levels fail at link time.
- Nested map/range iteration, in either nesting order, times out at both
  optimization levels. The exact programs are `map-in-for` and `for-in-map` in
  the integration test.

These six cases are strict expected failures, with the expected exception type
recorded; the other twelve Python controls pass. Fix these before expanding
container ownership integration, and remove each expected-failure marker when
its regression passes. Native cases have no expected-failure markers.

Evidence: `build/memory-ownership/range-continue/baseline-tests.log` records
22 failures (16 native and six bootstrap) and 14 passes before the native fix.
`candidate-tests.log` records 30 passes and the same six bootstrap failures before
they were marked. Later verification and promotion are recorded in the
[ownership work log](../memory-ownership/WORK_LOG.md).
