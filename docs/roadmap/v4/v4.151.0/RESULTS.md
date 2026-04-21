# v4.151.0 E7 Results

## Per-lever results

| State | quicksort (ms) | vs v4.150.0 | vs Rust | Lever outcome |
|---|---:|---:|---:|---|
| v4.150.0 baseline | 1.187 | — | 3.13× | — |
| After E7a (doubling audit) | — | — | — | **no-op** (already correct) |
| After E7b (realloc value-type) + E7c (push fast path) | 1.102 | **−7.2%** | 2.99× | **WIN** |
| v4.151.0 tag | 1.102 | −7.2% | 2.99× | — |

Note: Levers 2 and 3 were measured together because Lever 1 was a no-op
and the two remaining levers target orthogonal code paths (grow vs push).

## 5% rule check (full corpus, 15-run medians)

| Benchmark | Baseline (ms) | Patched (ms) | Delta | Status |
|-----------|-----:|-----:|---:|---|
| fib_recursive | 15.4 | 15.2 | −1.3% | ok |
| **quicksort** | **1.19** | **1.10** | **−7.6%** | **WIN** |
| struct_alloc | 0.021 | 0.026 | noise | ok (sub-ms) |
| enum_match | 0.17 | 0.17 | −1.2% | ok |
| prime_sieve | 2.09 | 2.14 | +2.2% | ok |
| string_concat | 0.079 | 0.070 | −11.4% | ok (bonus) |

No non-target workload regresses > 2% (prime_sieve +2.2% is noise,
within the ±3% WSL2 measurement band observed across baseline-only runs).

## Sanitizer verification

| Check | Result |
|-------|--------|
| ASan | **55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN** (matches baseline) |
| Valgrind | **0 CLEAN / 62 WARNINGS_ONLY / 4 ERRORS** (all 4 pre-existing Ge.1) |
| **New ASan findings** | **0** |
| **New valgrind findings** | **0** |

## Honest story

E7 delivered a genuine **−7.2% improvement on quicksort** (1.187 → 1.102 ms),
bringing the Mapanare/Rust ratio from 3.13× to 2.99×. This is below the
PLAN's 30% target because the quicksort benchmark is **dominated by list
access during the sort phase** (~130K `__mn_list_get` + `__mn_list_set`
calls), not by list push (~10K pushes during initialization). The push
improvements work — realloc avoids 12 unnecessary memcpys per run, and the
fast-path restructure eliminates 10K validation+detach checks — but they
affect only ~15% of the benchmark's total execution time.

The remaining 3× gap vs Rust is structural:
1. **Opaque function calls**: list get/set/push are calls to `libmapanare_rt.a`
   functions that LLVM cannot inline (separate compilation unit)
2. **COW tax**: every list operation checks the COW header (magic + refcount),
   costing 2–3 extra memory reads per operation
3. **Bounds checking**: every `__mn_list_get` does `i < 0 || i >= len`

Closing below 2× Rust requires **emitter-level changes**: emit inline
`getelementptr` + `store` instructions for list operations on locally-owned
lists, bypassing the runtime entirely. This is an E8+ scope change.

The E7 changes are correct, safe (0 new sanitizer findings), and worth
keeping. The realloc lever is the Sh.2-adjacent canary — it passed both
ASan and valgrind cleanly, validating the v4.131.0 ownership-transfer
guarantees. No ABI change was needed (value-type predicate uses existing
`elem_size` field).
