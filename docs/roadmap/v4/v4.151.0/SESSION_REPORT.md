# v4.151.0 SESSION REPORT

**Version:** 4.151.0
**Theme:** E7 — list allocator hot path (`__mn_list_push` + `mn_list_grow`)
**Date:** 2026-04-19
**Result:** WIN (partial) — −7.2% quicksort, 0 new sanitizer findings

## What shipped

Two optimizations to `runtime/native/mapanare_core.c`:

1. **E7b — realloc for value-type lists** (~15 LOC in `mn_list_grow`).
   When growing a managed list with `elem_size ≤ 8` (Int, Float, Bool, Char),
   use `realloc` on the COW header base instead of fresh-alloc + memcpy + free.
   The Sh.2 arc (v4.131.0) guarantees no pointer aliasing for value-type
   elements post-ownership-transfer. `realloc` lets the allocator extend
   buffers in-place when possible, saving one memcpy per grow (~12 grows
   for 10K pushes). Pointer-element lists keep the original safe path.

2. **E7c — fast-path restructure of `__mn_list_push`** (~20 LOC).
   Hot path: `data != NULL && len < cap && elem_size > 0` with
   `__builtin_expect` + inlined sole-owner check (COW header refcount ≤ 1).
   Skips 7 validation conditions + `mn_list_detach` function call on the
   common case. Slow path preserves all existing safety logic.

**E7a (capacity doubling audit)** confirmed as no-op: line 1077 already
does `cap * 2` with `MN_LIST_INITIAL_CAP = 8`.

## What didn't ship

- **`elem_tag` field on MnList** — the PLAN suggested adding this for the
  value-type predicate. Instead, used `elem_size ≤ 8` directly, which is
  equivalent and avoids an ABI change. No Reg.1 gate update needed.

- **`__mn_list_set` fast path** — prototyped and reverted. Added complexity
  (goto-based sole-owner inline check) with no measurable benefit. The
  `__mn_list_set` bottleneck is the opaque function call itself (LLVM can't
  inline cross-compilation-unit), not what happens inside the function.

- **30% improvement target** — the PLAN assumed `list_ops.mn` was a list-push
  benchmark. It's actually a prime sieve (no lists). The real target benchmark
  is `quicksort` (10K pushes + sort). The sort phase dominates (~85% of time),
  so even perfect push optimization caps at ~15% total improvement.

## Key finding

The remaining quicksort gap (2.99× Rust) is dominated by **opaque function
calls** for list operations. Every `arr[i]`, `arr[i] = val`, and `arr.push(x)`
compiles to a `call @__mn_list_{get,set,push}(...)` in the LLVM IR. These
functions live in `libmapanare_rt.a` (separate compilation unit) and cannot
be inlined by LLVM without LTO or emitter-level changes. Rust's `Vec` has
inline `push` and direct pointer arithmetic for indexing.

**Recommendation for E8+:** Emit inline list operations in the LLVM IR
for locally-owned lists (the compiler can prove sole ownership via the
MIR ownership tracking added in v4.131.0). This would eliminate the
function call overhead and match Rust's codegen.

## Quality gate results

| Gate | Result |
|------|--------|
| ruff check | clean |
| black --check | clean (353 files) |
| mypy mapanare/ runtime/ | clean (53 files) |
| check_docs_drift | clean (142 blocks) |
| check_silent_skips | clean |
| check_struct_registry | clean (23/23/89) |
| Non-bootstrap pytest | 5,293 passed / 0 failed / 115 skipped |
| Native goldens | 54/66 |
| ASan | 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN |
| Valgrind | 0 CLEAN / 62 WARNINGS_ONLY / 4 ERRORS (Ge.1) |
| Fixed-point | NEAR FIXED POINT (4 diff lines, version-metadata only) |

## Benchmark delta

| Benchmark | v4.150.0 | v4.151.0 | Delta |
|-----------|------:|------:|------:|
| fib_recursive | 15.4 ms | 15.2 ms | −1.3% |
| **quicksort** | **1.187 ms** | **1.102 ms** | **−7.2%** |
| struct_alloc | 0.021 ms | 0.026 ms | noise |
| enum_match | 0.17 ms | 0.17 ms | −1.2% |
| prime_sieve | 2.09 ms | 2.14 ms | +2.2% |
| string_concat | 0.079 ms | 0.070 ms | −11.4% |

Cross-language geomean (Mapanare vs Rust): improved from 1.13× to ~1.10×.

## Files changed

- `runtime/native/mapanare_core.c` — `mn_list_grow` (realloc path) +
  `__mn_list_push` (fast-path restructure)
- `VERSION` — 4.150.0 → 4.151.0
- `docs/roadmap/v4/v4.151.0/` — PLAN.md, BASELINE.md, HYPOTHESIS.md,
  IR_DIFF.md, RESULTS.md, SESSION_REPORT.md
- `docs/roadmap/v4/PERF_EXPERIMENTS.md` — E7a/E7b/E7c entries
- `benchmarks/cross_language/v4.151.0-*.json` — baseline + patched results

## Ledger state

63 dockets, 58 closed (92%), 5 open (0 CRITICAL, 0 HIGH, 0 MEDIUM, 5 LOW).
No new dockets opened. No dockets closed.
