# v4.146.0 Session Report — E2: fib_recursive calling convention

**Date:** 2026-04-18/19
**Duration:** ~2h (including two purity-check iterations)
**Verdict:** Dead end (hygiene patch kept)

## What we set out to do

Audit the LLVM IR emitted for `fib(n)` against Rust's `fib(n)`, identify
any missing IR flags or function attributes, patch them, and measure the
impact. The hypothesis was that missing `nsw`, `readnone`, or `noundef`
flags accounted for the remaining ~10% gap to Rust on `fib_recursive`.

## What we found

1. **`nsw` already present.** v4.30.0's claim that `nsw` was added to
   signed `add`/`sub`/`mul` is verified. Lines 2951-2953 of
   `emit_llvm_text.py` emit `add nsw`, `sub nsw`, `mul nsw` for all
   integer arithmetic. No gap here.

2. **LLVM infers everything.** After `opt -O2`, Mapanare's `fib` has
   identical attributes to Rust's: `nofree nosync nounwind willreturn
   memory(none)`, `fastcc` calling convention, and the accumulator
   tail-call transformation (one recursive call + loop). LLVM's
   FunctionAttrs pass and TailCallElim pass do this automatically.

3. **The gap is measurement, not codegen.** Mapanare fib_recursive uses
   external timing (subprocess spawn overhead ~1-3ms). Rust uses internal
   timing (Instant::now). At ~18ms computation, the 2ms subprocess
   overhead accounts for the entire 1.11× ratio.

## What we patched (hygiene, not perf)

Even though LLVM infers the attributes, explicitly declaring them is
good IR practice:

- **`noundef` on scalar parameters** (Int/Bool/Float). 3 logic lines in
  param-list builder. Safe because Mapanare has no undef-valued scalars
  (Option types cover nullable).

- **`memory(none) nofree nosync` on pure functions.** Fixed-point
  computation at module level (`_compute_pure_fns`). ~40 logic lines.
  Only marks functions with all-scalar signatures and no calls to
  impure functions. For the self-hosted compiler (38K+ lines), only
  21 constant-returning functions qualify (type-kind enum accessors).

## Debugging detour

The first purity implementation was too aggressive: it allowed calls to
any user-defined function (not just pure ones), causing the self-hosted
compiler binary to shrink from 3.57MB to 2.08MB and break completely
(0/66 goldens). Root cause: `memory(none)` on constructor functions
with `sret` parameters told LLVM the function didn't write to the
caller-provided return slot. LLVM eliminated the stores.

The fix was two-fold:
1. Fixed-point iteration: only mark a function pure if ALL its callees
   are themselves pure (Kildall-style dataflow).
2. Scalar-signature gate: only candidates with all-scalar params and
   scalar return type qualify. This excludes struct constructors, string
   builders, and anything touching pointer-level data.

After the fix: 54/66 goldens (matches baseline), 548/548 LLVM tests,
stage1 binary 3.57MB (matches baseline within 0.1%).

## Numbers

| Metric | Baseline | Patched | Delta |
|---|---:|---:|---:|
| fib_recursive wall (ms) | 20.045 | 19.892 | -0.8% |
| mnc-stage1 binary (bytes) | 3,570,832 | 3,566,736 | -0.1% |
| Goldens (pass/fail) | 54/12 | 54/12 | 0 |
| LLVM tests | 548/0 | 548/0 | 0 |

## What we learned

1. LLVM's interprocedural analysis is excellent for pure integer
   functions. Declaring attributes explicitly doesn't help when LLVM
   can infer them.

2. `memory(none)` is dangerous on unoptimized IR if the function
   signature involves pointers or structs. The attribute is about
   caller-visible effects, and `sret` is caller-visible.

3. The benchmark methodology gap (external vs internal timing) is the
   dominant source of error for short workloads. Future work should
   add `__BENCH_METRICS__` to Mapanare benchmark binaries.

## Files changed

- `mapanare/emit_llvm_text.py` — `_compute_pure_fns` (42 lines),
  `noundef` on scalar params (3 lines), `ret_nd` on scalar returns
  (4 lines), pure-fn attribute emission (3 lines). Total: ~52 logic
  lines.
