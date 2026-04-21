# v4.147.0 Baseline — E3 (parameter-level noalias)

## Wall time (median of 18 runs, trimmed, ms)

| Benchmark     | C (gcc) | C (clang) | Rust | Go    | Mapanare | Python  |
|---------------|---------|-----------|------|-------|----------|---------|
| fib_recursive | 10.795  | 18.209    | 18.338 | 34.305 | 23.347 | 779.875 |
| quicksort     | 0.342   | 0.341     | 0.368 | 0.388 | 2.384  | 78.442  |
| struct_alloc  | 0.571   | 0.017     | 0.016 | 0.020 | 1.159  | 201.269 |
| enum_match    | 0.130   | 0.144     | 0.284 | 0.194 | 1.344  | 77.584  |
| prime_sieve   | 1.941   | 1.735     | 1.756 | 2.004 | 3.395  | 369.382 |
| string_concat | 0.072   | 0.051     | 0.040 | 49.526 | 1.660 | 9.748  |

## Vectorization diagnostic (opt -O3 -pass-remarks)

| Benchmark    | Vectorized | Failed | Key failure reason |
|--------------|-----------|--------|-------------------|
| quicksort    | 0         | 5      | control flow cannot be substituted for a select |
| prime_sieve  | 0         | 1      | could not determine number of loop iterations |
| struct_alloc | 0         | 0      | no vectorizable loop body (function call barrier) |

## Sanitizer baseline

- **ASan:** 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN
- **Valgrind:** 0 CLEAN / 62 WARNINGS_ONLY / 4 ERRORS (Ge.1 residuals)
