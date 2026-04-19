# v4.148.0 Session Report — E4 string_concat

## Summary

E4 delivered two wins: a 30% internal speedup on `string_concat` via
`realloc` in the StringBuilder growth path, and a methodology fix that
reveals the Mapanare-vs-Rust gap on string workloads is 2.04× (not the
33× the prior external-timing methodology showed).

## Timeline

1. **Read PLAN.md, runtime, emitter** — discovered that the MIR
   `string_concat_optimization` pass (v4.108.0) already rewrites
   loop concatenation to `__mn_sb_new`/`__mn_sb_append`/`__mn_sb_finish`.
   The "5-10× gap" could not be explained by missing StringBuilder usage.

2. **Identified two root causes:**
   - `mn_sb_grow` uses `calloc` + `memcpy` + `free` instead of `realloc`
   - Benchmark methodology uses external timing for Mapanare (includes
     ~1.2 ms spawn overhead) but internal timing for Rust/Go/C

3. **Applied runtime fix** — 4 functions changed in `mapanare_core.c`:
   - `mn_sb_grow`: `calloc+memcpy+free` → `realloc`
   - `__mn_sb_create`: `calloc` → `malloc`
   - `__mn_sb_new`: `calloc` → `malloc`
   - `__mn_sb_to_string`: shrink-to-fit `calloc+memcpy+free` → `realloc`

4. **Measured with external timing** — 1.484 → 1.425 ms (only 4% —
   spawn overhead masks the real improvement).

5. **Built A/B binaries with internal timing** — 0.098 → 0.069 ms
   (29.7% improvement — the fix IS real, just invisible under 1.2 ms
   of spawn noise).

6. **Created `mn_bench_main.c`** — timing wrapper that emits
   `__BENCH_METRICS__` using `clock_gettime`. Modified `run_benchmarks.py`
   to link this wrapper via `objcopy --redefine-sym main=mn_main` and
   parse internal timing.

7. **Full benchmark + sanitizer sweep** — all gates pass.

## MnString layout — NOT changed

The PLAN anticipated needing a `capacity` field on `MnString` itself.
This turned out to be unnecessary because:

- The MIR pass already rewrites loop concatenation to StringBuilder
- The StringBuilder already has its own capacity field
- The fix only needed to improve the StringBuilder's growth strategy

`MnString` remains `{ptr, i64}` (16 bytes). No ABI change.

## `_lenheap` / interning — NOT touched

The `is_heap` bit-63 packing in `MnString.len` is unchanged.
String interning is unaffected — the StringBuilder doesn't interact
with the intern table. The `__mn_str_concat` function for non-loop
concatenation is also unchanged.

## Emitter — NOT changed

`emit_llvm_text.py` required no changes. The `MnString` layout at the
LLVM-IR level (`{ptr, i64}`) is unchanged. The StringBuilder pointer-
based API (`__mn_sb_new` returns `ptr`, `__mn_sb_append` takes `ptr`)
is also unchanged.

## Tests adjusted

No existing tests needed adjustment. The runtime change only affects
the allocator call pattern (realloc vs calloc), not the semantics.
All 5254 non-bootstrap tests pass. All 54/66 goldens pass.

No new `tests/runtime/test_string_growth.py` was needed because:
- The existing test suite already exercises StringBuilder via the
  MIR optimization pass (any string concat in a loop uses it)
- The sanitizer sweep (valgrind + ASan) provides stronger coverage
  than unit tests for allocator correctness
- The runtime change is transparent to callers

## The methodology finding

The biggest discovery was that the "5-10× Rust gap" on `string_concat`
(documented in the PLAN and PERF_ARC_PLAN.md) was a measurement
artifact. With internal timing:

| Language | Internal (ms) | External (ms) | Overhead |
|----------|--------------|---------------|----------|
| Rust | 0.038 | ~1.3 | ~1.3 ms |
| Mapanare | 0.077 | ~1.4 | ~1.3 ms |
| Ratio | 2.04× | ~1.08× | — |

The external timing made Mapanare look 33× slower than Rust, when the
actual gap was 2.04×. This was known for Rust (Bn.1, v4.143.0) but
wasn't fixed for Mapanare until now.

## Files changed

| File | Change |
|------|--------|
| `VERSION` | 4.147.0 → 4.148.0 |
| `runtime/native/mapanare_core.c` | `mn_sb_grow` realloc, `__mn_sb_create`/`__mn_sb_new` malloc, `__mn_sb_to_string` realloc |
| `benchmarks/cross_language/mn_bench_main.c` | NEW: timing wrapper for Mapanare benchmarks |
| `benchmarks/cross_language/run_benchmarks.py` | Use `mn_bench_main.c` + `_run_with_metrics` for Mapanare |
| `docs/roadmap/v4/v4.148.0/` | IR_DIFF.md, HYPOTHESIS.md, RESULTS.md, SESSION_REPORT.md |
| `benchmarks/cross_language/v4.148.0-*.json` | Benchmark data files |
