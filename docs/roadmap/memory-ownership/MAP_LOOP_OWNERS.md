# Map results in loops

The Python compiler now bounds the lifetime of proven factory results when
their previous value has no live or escaping aliases at the next allocation.
The original `map_return_loop_lifetime.mn` reproducer leaked 535,464 bytes in
1,998 allocations over 1,000 iterations. It now prints `3000` with no sanitizer
errors or leaks at Python O0–O3.

## Proof and cleanup

`recyclable_map_results` runs on optimized MIR before function emission. It
considers calls to the existing proven fresh-map factories, in blocks belonging
to a control-flow cycle. A backward liveness fixed point includes all Value
operands. Phi inputs are conservatively live on every predecessor.

Copy/Phi relationships form an alias group. The group must have exactly one
allocation origin, no parameter origin, and no member live before that allocation.
Only copies, phis, and `len` may consume its values. Unknown calls, aggregate
captures, returns, moves, map iterators and other borrowed views are rejected.
Malformed control-flow targets and async functions are also rejected. This is
deliberately narrower than general map ownership or reference counting.

Every qualifying allocation gets a private owner slot initialized to null in
the function entry. Slots are registered before any block is emitted, so return
cleanup sees them regardless of block order. Ordinary Copy bookkeeping cannot
move or remove this owner. After the next factory call returns, the emitter
releases the previous handle and saves the new one. Existing map drop glue frees
the final handle on every return; skipped sites safely free null.

At most one old handle per eligible site remains between calls; a newly created
handle briefly coexists with it during replacement. Aliases may still share a
map within the current iteration. The proof requires them to be dead before
reclaiming it, so no runtime retain/clone API or container layout change is needed.

## Verification

`test_map_loop_ownership.py` runs eight programs at Python O0–O3 with generated
code and the C core instrumented by ASan/UBSan, with leak detection enabled.
All 32 leak on the committed baseline and pass after the fix. Cases cover the
original loop, aliases, conditional sites, nested loops with independent sites,
break/continue, early returns, skipped loops and discarded results.

Four additional executions retain an alias across iterations. They verify output
and invalid-access safety, and assert that recycling was declined. Leak detection
is disabled only for those guards because legacy escaping-map ownership remains
open. Twenty-three MIR controls include captures, map iteration, and a
single-origin branch where skipping one copy changes the liveness decision.

Evidence: `build/memory-ownership/map-loop-owners/`. Broader LLVM/MIR and ownership
suites are recorded in [WORK_LOG.md](WORK_LOG.md). No native source or runtime
code changed; Windows/macOS execution was not qualified by these Linux/WSL tests.

## Next boundary

Escaping aliases, groups with multiple allocation origins, mutable replacement,
map iteration/borrowed views, and nested element ownership keep their previous
behavior. Fixing these requires explicit transfer/retain/clone semantics or a
stronger proof that follows derived views. Do not remove the conservative guards
or free every overwritten map variable. Native map cleanup and owned-container
constructor adoption remain separate work.
