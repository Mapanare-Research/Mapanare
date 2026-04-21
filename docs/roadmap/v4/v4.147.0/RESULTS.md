# v4.147.0 Results — E3 (parameter-level noalias)

## Headline

**DEAD END.** Parameter-level `noalias` is structurally inapplicable to
the target benchmarks. LLVM's `noalias` attribute only applies to
pointer-typed (`ptr`) parameters. Mapanare passes `List<T>`, `String`,
`Map<K,V>`, and small structs as LLVM aggregates by value (e.g.,
`{ptr, i64, i64, i64, i64}` for List, 40 bytes) because they are under
the 64-byte byref threshold. No target benchmark function has a `ptr`
user parameter. The emitted IR is **byte-identical** before and after
the patch for all six benchmarks.

## Standard benchmark (20 runs, external timing)

| Workload      | Baseline (ms) | Patched (ms) | Delta   |
|---------------|--------------|-------------|---------|
| **quicksort** | **2.384**    | **2.543**   | **+6.7%** (subprocess-spawn noise) |
| **prime_sieve** | **3.395**  | **3.264**   | **-3.9%** (noise) |
| **struct_alloc** | **1.159** | **1.178**   | **+1.6%** (noise) |
| fib_recursive | 23.347       | 20.257      | -13.2% (noise) |
| enum_match    | 1.344        | 1.393       | +3.6% (noise) |
| string_concat | 1.660        | 1.335       | -19.6% (noise) |

All deltas are subprocess-spawn variance. The Mapanare binary is
byte-identical (same IR, same clang invocation). The fib_recursive
and string_concat swings confirm these are measurement artifacts.

## Escape-analysis hit count

| Function | Params marked | Reason |
|----------|--------------|--------|
| `partition(arr: List<Int>)` | 1 (`noalias_ok`) | Non-escaping, non-recursive, distinct call-site args |
| `qsort(arr: List<Int>)` | 0 | Recursive self-call with same param |
| `is_prime(n: Int)` | 0 | Scalar param (Int) — noalias inapplicable |
| `main()` | 0 | Skipped (main always skipped) |

**Total across target benchmarks: 1 parameter marked, 0 emitted as `noalias`.**

The MIR-level pass correctly identifies `partition(arr)` as non-aliasing.
But the emitter correctly does NOT emit `noalias` because the LLVM type
`{ptr, i64, i64, i64, i64}` is an aggregate, not a pointer.

## Vectorization remark delta

| Benchmark    | Before | After | Delta |
|--------------|--------|-------|-------|
| quicksort    | 0 vec / 5 fail | 0 vec / 5 fail | no change |
| prime_sieve  | 0 vec / 1 fail | 0 vec / 1 fail | no change |
| struct_alloc | 0 vec / 0 fail | 0 vec / 0 fail | no change |

## Sanitizer delta

| Sweep | Before | After | Delta |
|-------|--------|-------|-------|
| ASan ASAN_ERROR | 0 | 0 | **+0** (clean) |
| Valgrind ERRORS | 4 | 4 | **+0** (clean) |

## Why this was a dead end

1. **LLVM `noalias` only applies to pointer-typed parameters.** The
   attribute is defined in the LLVM LangRef as: "This indicates that
   objects accessed via pointer values based on the argument ... are not
   also accessed, during the execution of the function, via pointer
   values not based on the argument." The key phrase is "pointer values
   based on the argument" — the argument must BE a pointer.

2. **Mapanare passes compound types by value, not by reference.** The
   `_BYREF_BYTES = 64` threshold means all types under 64 bytes are
   passed as LLVM aggregates (`{ptr, i64, i64, i64, i64}` for List,
   `{ptr, i64}` for String, etc.). These are value types in LLVM's
   type system, not pointer types.

3. **The vectorization barriers are not aliasing.** Even if `noalias`
   could be applied, the `loop-vectorize` pass fails for unrelated
   reasons: control flow complexity (quicksort), unknown trip count
   (prime_sieve), and function call barriers (struct_alloc).

## What the pass DOES do correctly

The `mark_noalias_params` pass (134 logic lines in `mir_opt.py`) is
sound and will emit `noalias` when two conditions are met:
1. The MIR escape analysis proves the parameter non-aliasing
2. The LLVM parameter type is `ptr` (byref or closure env pointer)

Currently only closure env pointers (`ptr %__env_ptr`) satisfy both
conditions. The pass is kept for:
- Future work on byref threshold reduction (E5/ABI.1)
- Closure-heavy workloads where env pointer aliasing blocks optimization

## 5% rule

- Target benchmarks: 0% improvement (binary identical)
- No benchmark regresses > 2% (all deltas are subprocess-spawn noise)
- **Decision: keep pass (zero risk, zero perf impact), close E3 as dead end**

## Verdict

**DEAD END.** The experiment ruled out parameter-level `noalias` as a
lever for the target benchmarks. The root cause is the by-value ABI for
compound types, not a missing attribute. The correct fix is ABI.1
(v4.149.0 E5: pass large structs by reference, enabling both `noalias`
and pointer-based optimizations). See PERF_EXPERIMENTS.md entry.
