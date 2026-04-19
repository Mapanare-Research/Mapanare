# E2 Hypothesis

## Original hypothesis (pre-IR-diff)

> Adding `nsw` to signed `add`/`sub`/`mul` and `readnone` + `speculatable` +
> `willreturn` to pure functions like `fib` closes <= 10% of the `fib_recursive`
> gap.

## Revised hypothesis (post-IR-diff)

> **The calling convention is already clean. The ~10% gap is not in `fib`.**

**Evidence:**

1. `nsw` is already emitted on `add`/`sub`/`mul` (v4.30.0 claim verified).
2. LLVM infers `memory(none) nofree nosync fastcc` on `fib` during `-O2`.
3. LLVM applies the accumulator tail-call transformation identically for
   both Mapanare and Rust — 3 blocks, 1 recursive call, PHI-based loop.
4. The optimized IR is structurally identical between the two compilers.
5. The only difference is `noundef` on params/return (no codegen impact for `i64`).
6. The 1.11x gap (20.045 vs 18.042 ms) = 2.0ms delta, consistent with
   subprocess-spawn overhead in external timing methodology.

**Remaining patch (hygiene, not perf):**

Even though LLVM infers purity, explicitly emitting `noundef` on scalar
parameters and `memory(none)` on pure functions is good IR hygiene:

- `noundef` on `Int`/`Bool`/`Float` params: tells LLVM no poison/undef values
  exist in Mapanare scalar paths (true — we have Option types instead)
- Explicit pure-fn attributes: lets LLVM use purity info earlier in the
  optimization pipeline, potentially helping other workloads

**Expected delta on fib_recursive:** < 1%, within noise. E2 closes as
**dead end** for this workload. The hygiene patch is kept for correctness.

## Files to edit

1. `mapanare/emit_llvm_text.py` — `noundef` on scalar params, pure-fn detection
