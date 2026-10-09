# Direct map return ownership

The Python LLVM emitter previously freed a local map before returning its
handle. The caller then accessed released storage. Suppressing that free alone
would leak the result because user-function map results were never tracked by
caller cleanup.

Legacy direct Map returns compare each tracked local map with the returned pointer.
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
The native emitter is unchanged by these Python emitter milestones.

## Retained local groups

Closed fresh-map alias groups now transfer exactly one retained reference to
the caller. Return cleanup releases every local reference slot, including slots
holding the same pointer as the returned map. Skipping all matching slots would
leak one reference per surviving alias. Unrelated groups are also released.
Legacy owner slots keep pointer-based escape handling; parameter aliases,
unknown captures and uncertain origins cannot enter the retained group.

`test_shared_map_returns.py` runs six programs at O0–O3: retaining the first map,
skipped loops, early returns, multiple independent groups, forwarding wrappers,
and heap String keys. All 24 pass with exact output and ASan/UBSan/LSan; 20 leaked
before integration. Sixteen MIR proof controls pass. Broad validation passes
1,730 tests, with seven skips and five expected failures. Evidence lives in
`build/memory-ownership/retained-map-emitter/returns-*.log`.

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

The original loop replacement reproducer is now fixed for proven nonescaping
factory results: [MAP_LOOP_OWNERS.md](MAP_LOOP_OWNERS.md) describes the liveness
proof and private owner slots. Its former 535,464-byte leak is absent at O0–O3.
Variable-based cleanup remains the fallback for cases outside that proof.

Do not simply free the previous handle before every store: copies and captured
aliases may still reference it. Broader sharing still needs transfer or
retain/clone rules, including branch-sensitive cleanup. Mixed fresh/borrowed
returns, maps nested in aggregate returns, native map cleanup, and recursive
element ownership remain open. The installed native fixed-point compiler stays
at the previously verified hash because this milestone changes only Python.
