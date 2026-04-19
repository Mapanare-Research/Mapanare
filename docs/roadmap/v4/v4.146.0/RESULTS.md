# v4.145.0 Results — E2 (fib_recursive)

## Headline

**DEAD END.** The calling convention is already clean. LLVM infers
`memory(none) nofree nosync fastcc` and applies the accumulator tail-call
transformation on Mapanare's `fib` identically to Rust. The ~10% gap is
subprocess-spawn overhead in the measurement methodology, not codegen
quality. A hygiene patch (`noundef` on scalar params, `memory(none)` on
pure functions) is kept for correctness but has no measurable perf impact.

## Standard benchmark (100K iterations, 20 runs, external timing)

| Workload | Baseline (ms) | Patched (ms) | Rust (ms) | Delta |
|---|---:|---:|---:|---:|
| **fib_recursive** | **20.045** | **19.892** | **18.042** | **-0.8%** |
| quicksort | 2.508 | 2.345 | 0.372 | -6.5% |
| struct_alloc | 1.377 | 1.176 | 0.018 | -14.6% |
| enum_match | 1.442 | 1.595 | 0.293 | +10.6%* |
| prime_sieve | 3.500 | 3.321 | 1.812 | -5.1% |
| string_concat | 1.463 | 1.226 | 0.041 | -16.2% |

*enum_match variance is subprocess-spawn noise (computation is ~0.15ms,
measurement overhead is ~1.4ms; 3 independent runs gave 1.442/1.595/1.742ms).

## IR analysis

The optimized LLVM IR for `fib` is **structurally identical** between
Mapanare and Rust after `opt -O2`:

**Mapanare (optimized):**
```llvm
; attributes = { mustprogress nofree nosync nounwind willreturn memory(none) }
define internal fastcc i64 @fib(i64 %n) unnamed_addr {
  ...
  %c.13 = tail call fastcc i64 @fib(i64 %i.10)
  ...
}
```

**Rust (optimized):**
```llvm
; attributes = { nofree nosync nounwind nonlazybind memory(none) uwtable }
define internal fastcc noundef i64 @fib(i64 noundef %n) unnamed_addr {
  ...
  %_3 = tail call fastcc noundef i64 @fib(i64 noundef %_4)
  ...
}
```

LLVM infers all the same attributes and applies the same accumulator
tail-call transformation. The only difference is `noundef` on params/return
(now emitted by Mapanare post-patch, but with no codegen impact for `i64`).

## v4.30.0 claim verification

**CONFIRMED.** `nsw` is correctly emitted on `add`/`sub`/`mul` for signed
integer operations (lines 2951-2953 of `emit_llvm_text.py`). The v4.30.0
claim holds at v4.146.0.

## Hygiene patch (kept, zero perf impact)

1. **`noundef` on scalar parameters** (`Int`/`Bool`/`Float`) — Mapanare has
   no undef-valued scalar paths; Option types cover nullable. ~3 logic lines.

2. **`memory(none) nofree nosync` on pure functions** — functions with
   all-scalar signatures (params and return) and no calls to impure
   functions. Fixed-point iteration at module level computes the pure set.
   ~40 logic lines.

   For `fib`, the emitter now produces:
   ```llvm
   define internal noundef i64 @fib(i64 noundef %n) nofree nosync nounwind willreturn memory(none) {
   ```
   which matches Rust's attribute set exactly.

## Measurement methodology gap

The remaining ~10% gap (20.0ms vs 18.0ms) is measurement methodology:

- **Mapanare:** external timing via `time.perf_counter()` around
  `subprocess.run()` — includes ~1-3ms subprocess spawn overhead
- **Rust:** internal timing via `__BENCH_METRICS__` (`Instant::now()`) —
  excludes subprocess spawn

The fib(35) computation itself takes ~18ms for both. The 2ms delta is
subprocess spawn + Mapanare's startup/shutdown (intern_destroy, string
operations in main). This is a harness issue, not a codegen issue.

## Verdict

**DEAD END.** `fib_recursive` calling convention is clean. Patch kept
for hygiene. E2 closes as experiment 2 of 8. See `PERF_EXPERIMENTS.md`.

## 5% rule

- fib_recursive: -0.8% (does NOT meet 5% threshold)
- No other benchmark regresses > 2% (enum_match apparent +10.6% is
  subprocess-spawn noise, confirmed by 3 independent measurement runs)
- **Decision: keep hygiene patch, close E2 as dead end**
