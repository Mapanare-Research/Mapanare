# Boa — Python/DX Review (Arc 12)

**Grade: 8/10**
**Verdict: PASS WITH NOTES**

## Assessment

### Optimizer observability

**MIRPassStats:** All 12 counters are functional, including the new `allocations_promoted`. The `total_changes` property correctly sums all counters. Users (and future tooling) can inspect what the optimizer did to their code.

**Non-convergence error:** The `MIROptimizerNonConvergence` exception provides a clear diagnostic: names the function, the iteration cap, and instructs developers to find the ping-ponging passes. This is excellent DX for compiler developers debugging optimizer issues.

**Missing: per-function stats.** The current stats are module-level aggregates. There's no way to ask "which function had the most inlining?" or "which allocations were promoted?" For optimizer debugging, per-function stats would be valuable. Not blocking.

### Annotation support

**`@noinline`:** Not implemented. The inliner has a cost model that excludes large or recursive functions, but there's no user-facing way to prevent inlining of a specific function. For a compiler targeting systems programming, `@noinline` is eventually needed (e.g., for debugging hot loops where inlining obscures the profile).

**`@pure`:** Not implemented. The LICM pass (disabled) would benefit from purity annotations to know which functions are safe to hoist out of loops. Without `@pure`, LICM must conservatively assume all calls have side effects.

**Neither annotation is blocking for Arc 12** — they're future work that would unlock more aggressive optimization.

### Test quality

The 12 escape analysis tests cover all 6 escape criteria plus idempotency, mixed escaping/non-escaping, copy aliasing, and integration with the O2 pipeline. Test names are descriptive (`test_closure_capture_escapes`, `test_non_capturing_call_no_escape`). The helper functions (`_v`, `_const_int`, `_simple_fn`) make tests readable.

The inlining and strength reduction passes have fewer dedicated tests (relying on integration tests). This is acceptable given their simplicity but could be strengthened.

### LICM disabled state

The LICM pass is built but disabled via a comment in `optimize_function`. This is fine engineering — ship the infrastructure, gate the transform. However, there's no `--enable-licm` flag or similar mechanism for developers to experiment with it. The only way to enable LICM is to edit `mir_opt.py`. This is acceptable for now but should be a flag if LICM is planned for re-enablement.

## Items

| Item | Priority | Notes |
|------|----------|-------|
| `@noinline` annotation | MEDIUM | User control over inlining decisions |
| `@pure` annotation | MEDIUM | Enables LICM and more aggressive hoisting |
| Per-function pass stats | LOW | Useful for optimizer debugging |
| LICM enable flag | LOW | Currently requires source edit to enable |

## Score justification

8/10 — good observability through MIRPassStats and error messages. Test quality is solid. Deduction for missing user-facing annotations (@noinline, @pure) that would complete the optimizer's user interface. These are future work, not bugs.
