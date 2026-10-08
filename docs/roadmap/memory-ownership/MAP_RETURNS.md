# Direct map return ownership

The Python LLVM emitter previously freed a local map before returning its
handle. The caller then accessed released storage. Suppressing that free alone
would leak the result because user-function map results were never tracked by
caller cleanup.

Direct Map returns now compare each tracked local map with the returned pointer.
Only the matching handle escapes; unrelated maps still get freed. Runtime
comparison handles aliases and conditional returns. Private iterator cleanup
still runs before map cleanup, including an early return from a map loop.

Before emitting bodies, `owned_map_factories` proves which functions return
fresh map allocations on every return path. It follows local MapInit, copies,
phi inputs and already-proven factory calls. Repeated fixed-point passes cover
forward-defined wrappers. Every definition of a reused name must qualify.
Parameters, unknown/indirect calls, cycles, mixed borrowed/fresh results,
aggregate captures, unsupported instructions and alias chains of 64 or more
steps remain unproven. Current construction coverage is scalar/String keys and
values; nested resource ownership needs its own contract.

Callers track results from proven factories through the existing map cleanup
mechanism. Borrowed and uncertain results keep their previous behavior. This
summary proves ownership of the map handle; it does not establish ownership of
String or nested-container elements, and it does not enable owned constructors.
The native emitter and runtime are unchanged.

## Verification

`test_map_return_ownership.py` runs seven programs at Python O0–O3, with both
generated code and the C core instrumented by ASan/UBSan and leak detection
enabled. It covers the original fixture, aliases, forward wrappers, discarded
results, sibling maps with early returns through iteration, borrowed results,
and repeated factory calls separated by function cleanup. Twenty checks fail
against the original emitter; all 28 pass after the fix. The eight baseline
passes are borrowed-result and discarded-result controls.

`tests/mir/test_map_ownership.py` has thirteen proof controls, including mixed
returns, recursive/unknown callees, captures, future instructions and long alias
chains. All pass. Evidence lives under `build/memory-ownership/map-returns/`.

## Remaining lifetime work

The existing variable-based map cleanup retains only the last value assigned to
a slot. Repeated factory calls inside one function can therefore leak prior
results. `tests/native/fixtures/map_return_loop_lifetime.mn` prints `3000` but
LeakSanitizer reports 535,464 bytes in 1,998 allocations after 1,000 iterations.
This is the next concrete regression to fix.

Do not simply free the previous handle before every store: copies and captured
aliases may still reference it. Establish explicit owner slots and transfer or
retain/clone rules first, including branch-sensitive cleanup. Mixed fresh/borrowed
returns, maps nested in aggregate returns, native map cleanup, and recursive
element ownership remain open. The installed native fixed-point compiler stays
at the previously verified hash because this milestone changes only Python.
