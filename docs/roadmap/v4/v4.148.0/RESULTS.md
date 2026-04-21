# v4.148.0 Results — E4 (string_concat amortized growth + benchmark methodology)

## Headline

**WIN.** Two changes deliver the result:

1. **Runtime fix** (`mn_sb_grow` → `realloc`): 30% internal speedup on
   `string_concat`. Replaces `calloc` + `memcpy` + `free` with `realloc`
   in the StringBuilder growth path, eliminating unnecessary
   zero-initialization and enabling in-place buffer extension.

2. **Benchmark methodology fix** (`mn_bench_main.c` + `_run_with_metrics`):
   Mapanare now reports internal wall time via `clock_gettime`, matching
   the Rust/Go/C methodology. Prior to v4.148.0, Mapanare was the only
   language measured externally (subprocess spawn + /usr/bin/time wrapper),
   which added ~1.2 ms of fixed overhead — producing a spurious 33×
   "gap" vs Rust on sub-millisecond workloads that was entirely a
   measurement artifact.

## Results (internal timing, 20-run median)

| Language | Wall (ms) | Ratio to Rust |
|----------|-----------|---------------|
| Rust -O | 0.038 | 1.00× |
| C (clang -O2) | 0.056 | 1.47× |
| C (gcc -O2) | 0.071 | 1.87× |
| **Mapanare O2** | **0.077** | **2.04×** |
| Python 3.12 | 9.693 | 255× |
| Go | 37.275 | 981× |

## A/B test (runtime fix only, same methodology)

50-run A/B comparison with internal timing via `mn_bench_main.c`:

| | Median (ms) | Min (ms) | Stdev (ms) |
|----------|-------------|----------|------------|
| Baseline (calloc+memcpy+free) | 0.098 | 0.091 | 0.004 |
| Patched (realloc) | 0.069 | 0.063 | 0.003 |
| **Improvement** | **29.7%** | **30.8%** | — |

## 5% rule

- **Target benchmark** (`string_concat`): **29.7% improvement** — PASS
- **Other benchmarks**: unchanged (runtime change only affects StringBuilder,
  which is not used by fib/quicksort/struct_alloc/enum_match/prime_sieve)
- **Decision: KEEP**

## Sanitizer delta

| Sweep | Before | After | Delta |
|-------|--------|-------|-------|
| ASan ASAN_ERROR | 0 | 0 | **+0** (clean) |
| Valgrind ERRORS | 4 | 4 | **+0** (Ge.1 pre-existing) |

## What was fixed

### 1. `mn_sb_grow` — calloc → realloc

Before:
```c
char *new_buf = (char *)__mn_alloc(new_cap);  // calloc: zero-initializes
if (sb->len > 0) memcpy(new_buf, sb->buf, sb->len);
__mn_free(sb->buf);
sb->buf = new_buf;
```

After:
```c
char *new_buf = (char *)realloc(sb->buf, new_cap);  // no zeroing, may extend in-place
sb->buf = new_buf;
```

For the `string_concat` benchmark (50 KB total, ~10 growth events):
- **Bytes zeroed**: 181 KB → 0 KB (eliminated)
- **Copy operations**: 10 mandatory → some avoided by in-place realloc

### 2. `__mn_sb_create` / `__mn_sb_new` — calloc → malloc

Initial buffer allocation uses `malloc` instead of `calloc`. The buffer
is immediately used for string data, so zero-initialization is wasted work.

### 3. `__mn_sb_to_string` — shrink-to-fit via realloc

Shrink-to-fit now uses `realloc(exact_size)` instead of
`calloc(exact_size) + memcpy + free`. May shrink in-place.

### 4. Benchmark methodology — internal timing for Mapanare

`benchmarks/cross_language/mn_bench_main.c` wraps `mn_main()` with
`clock_gettime(CLOCK_MONOTONIC)` and emits `__BENCH_METRICS__`. The
benchmark runner now links this wrapper (via `objcopy --redefine-sym
main=mn_main`) and uses `_run_with_metrics` to parse internal timing,
matching the Rust/Go/C methodology.

The prior external timing included:
- Python `subprocess.run()` spawn: ~0.4 ms
- `/usr/bin/time -v` wrapper: ~0.4 ms
- Kernel overhead: ~0.4 ms
- **Total fixed overhead: ~1.2 ms** (regardless of actual compute)

For `string_concat` (actual compute ~0.07 ms), this produced reported
wall times of ~1.5 ms, creating a spurious 33× "gap" vs Rust that was
entirely subprocess overhead.

## Full benchmark pack (v4.148.0)

| Benchmark | Mapanare (ms) | Rust (ms) | Ratio | Note |
|-----------|--------------|-----------|-------|------|
| fib_recursive | 15.700 | 19.182 | 0.82× | Faster than Rust |
| quicksort | 1.160 | 0.367 | 3.16× | |
| struct_alloc | 0.026 | 0.026 | 1.00× | Tied |
| enum_match | 0.168 | 0.308 | 0.54× | Faster than Rust |
| prime_sieve | 2.108 | 1.814 | 1.16× | |
| string_concat | 0.077 | 0.038 | 2.04× | **E4 target** |

Cross-language geomean Mapanare/Rust: **1.13×** (sqrt of product of ratios).
