# v4.145.0 Session Report — E1: enum_match codegen vs Rust

**Date:** 2026-04-18
**Theme:** First experiment of the perf arc (v4.144.0 → v4.154.0)
**Verdict:** WIN — unified-return optimization merges two switches into one

---

## What the IR diff showed

The PLAN hypothesized that Mapanare emits cascaded `icmp eq`/`br i1`
chains for `match` while Rust emits a single `switch`. This was wrong.
The v4.34.0 decision-tree compiler already emits `switch i64` for flat
enum matches.

The actual gap: after LLVM -O2 inlines both `make_shape` and `area` into
`main`, Mapanare's loop has **two switches** while Rust's has **one**.
Rust's LLVM fuses the dispatch because the enum never materializes as
an intermediate aggregate. Mapanare constructs `{i64, i64, i64}` via
`insertvalue` chains, merges them through a PHI of aggregates, then
`extractvalue`s the tag and switches again.

LLVM's `InstCombine` can fold `extractvalue(insertvalue(base, val, idx), idx)`
→ `val`, but NOT `extractvalue(PHI(insertvalue..., insertvalue...), idx)` —
it does not distribute `extractvalue` into PHI arms. This is the root cause.

## What the hypothesis predicted

Unifying all return points through a single result alloca would:
1. Replace the aggregate PHI with per-field scalar PHIs (via SROA + mem2reg)
2. Make the tag a PHI of constants (0, 1, 2, 3, 4, 5)
3. Allow InstCombine to fold `extractvalue(insertvalue(PHI), 0)` → `tag_PHI`
4. Allow SimplifyCFG to merge the two switches into one

Expected delta: ~40–60% of match-loop time.

## What the patch did

Three edit points in `mapanare/emit_llvm_text.py` (~30 logic lines):

1. **`_emit_fn`** (function start): detect if return type is an inline
   enum (via `_enum_inline` registry). If so, create `%__ret_alloca` in
   the function's pre-entry block and set `_fn_unified_ret = True`.

2. **`_do_ret`** (return handler): when unified-ret is active, store the
   return value to `%__ret_alloca` and branch to `%__unified_ret` instead
   of directly emitting `ret`.

3. **Function assembly**: after all MIR blocks, emit the
   `%__unified_ret` block that loads from `%__ret_alloca` and returns.

The function still returns `{i64, i64, i64}` by value — no ABI change.
The enum layout is byte-identical to v4.140.0 Cb.5 verification.

## How the numbers moved

**Optimized IR:** Mapanare's `main` loop went from 88 lines / 2 switches
to 55 lines / 1 switch. The optimized IR is now structurally identical to
Rust's: one switch dispatching directly to per-arm computation blocks.
Bonus: LLVM now converts `sdiv i64 %x, 2` → `lshr i32 %x, 1` (the `nuw nsw`
flags on the narrowed arithmetic prove non-negativity).

**10M-iteration measurement** (amplified to isolate from subprocess overhead):
- Baseline (2-switch): 17.31 ms
- Patched (1-switch): 15.91 ms → **8.4% improvement**
- Rust -O: 30.74 ms (slower — Mapanare's i32-narrowed modulo is faster)
- C gcc -O2: 14.25 ms (Mapanare is 1.12× of C)

**Standard 100K-iteration measurement** (benchmark runner):
The improvement is masked by ~0.6 ms subprocess-spawn overhead that
dominates the ~0.15 ms computation. The benchmark runner uses external
timing (`perf_counter` around `subprocess.run()`) for Mapanare while
Rust/C/Go emit `__BENCH_METRICS__` with internal wall time. This
systematic bias makes Mapanare look ~1 ms slower than it actually is
for sub-millisecond workloads. Addressing this methodology gap is noted
for the pre-panel refresh at v4.153.0.

## What this means for the perf arc

The v4.145.0 E1 experiment proved the experiment loop works end-to-end:
measure → diff IR → form hypothesis → patch → re-measure → record. It
also surfaced a benchmark methodology issue (subprocess overhead) that
needs to be addressed before the v4.154.0 panel.

The unified-return optimization is general: it benefits all functions
returning inline enums, not just `area`/`make_shape`. Any hot loop that
constructs an inline enum in one function and matches on it in another
will see the same switch-merging benefit after inlining.

## Quality gates

| Gate | Result |
|---|---|
| Non-bootstrap pytest | 5225 passed / 0 failed / 115 skipped / 9 xfailed |
| Bootstrap pytest | 212 / 13 byte-identical |
| Goldens (mnc-stage1) | 54 / 66 (unchanged from v4.144.0) |
| Fixed-point | NEAR FIXED POINT (4-line Dr.1 diff, 0.004%) |
| ruff check | 0 errors |
| black --check | 0 reformats |
| Enum golden 07_enum_match | PASS (byte-identical through mnc-stage1) |
| Enum golden 27_enum_payload | Included in 54/66 pass set |

## Carry-forward

- **Methodology fix** (bench timing): Mapanare binaries should emit
  `__BENCH_METRICS__` internally (via C runtime `clock_gettime` +
  `getrusage` wrappers) so the benchmark runner uses `_run_with_metrics`
  instead of `_run_external`. This would correct the systematic ~1 ms
  bias on sub-millisecond workloads. Deferred to v4.153.0 pre-panel.

- **Self-hosted parity**: The unified-return change is Python-emitter
  only. A follow-up docket should mirror it into `emit_llvm.mn`. Severity
  LOW — the self-hosted path doesn't run the benchmark suite.

## Diff summary

```
mapanare/emit_llvm_text.py  | ~30 lines added
  _emit_fn                  | detect inline-enum return, create __ret_alloca
  _do_ret                   | store + br %__unified_ret instead of ret
  function assembly         | emit __unified_ret block (load + ret)
  ensure-terminated         | handle unified-ret case
```
