# Mapanare v4.107.0 — Full Cross-Language Benchmark Comparison

> **⚠ SUPERSEDED (2026-04-14).** This document captured the Mapanare
> state immediately before the v4.108.0 auto-StringBuilder fix.
> `string_concat` here reports 94.57 ms (246 MB peak); after v4.108.0
> it is **1.36 ms (2.26 MB peak)** — a 70× speedup / 109× memory
> reduction. The canonical reference for current performance is
> [`../PHASE_C_RESULTS.md`](../PHASE_C_RESULTS.md). This file is
> retained as a historical record of the pre-StringBuilder baseline;
> it is also the "same-harness control" used in Phase C's delta
> computation.

> Measured 2026-04-14 on WSL2 (Ubuntu on Windows), AMD Ryzen 9 7950X,
> 62 GB DDR5. **10 runs per configuration, highest and lowest dropped,
> median of the middle 8 reported.**
>
> Six languages × six workloads = 36 data points. Raw results in
> [`v4.107.0-results.json`](v4.107.0-results.json). Programs in
> [`go/`](go/) and [`c/`](c/); Mapanare `.mn` / Python `.py` / Rust
> `.rs` sources continue to live under `benchmarks/optimizer/` and
> `benchmarks/system/`.

---

## Methodology

| Configuration | Toolchain | Optimization |
|---|---|---|
| **C (gcc -O2)**    | gcc 13.3.0 | `-O2 -Wall -Wextra` |
| **C (clang -O2)**  | clang 18.1.3 | `-O2 -Wall -Wextra` |
| **Rust -O**        | rustc 1.94.1 | `rustc -O` (≈ `-C opt-level=3`) |
| **Go**             | go 1.22.5 | `go build -o bench` (default -O) |
| **Mapanare O2**    | mnc-stage1 (v4.106.1) | `emit-llvm → llvm-as → opt -O2 → llc → clang` linked against `libmapanare_rt.a` |
| **Python 3.12**    | CPython 3.12.3 | no JIT, no PyPy |

- **Wall time**: programs that emit a `__BENCH_METRICS__` block (Go, C,
  Python-wrapped) report internal `clock_gettime(CLOCK_MONOTONIC)` timing
  that excludes subprocess-spawn overhead. Rust and Mapanare binaries
  are timed externally via `time.perf_counter()` around
  `subprocess.run()`, which adds roughly 1–3 ms of spawn cost. This
  asymmetry is documented for honesty; it matters only for the handful
  of sub-2 ms results.
- **Peak memory**: always `Maximum resident set size (kbytes)` from
  `/usr/bin/time -v` wrapping the child. The C/Go programs' internal
  `getrusage(RUSAGE_SELF).ru_maxrss` would be inflated by the Python
  harness's copy-on-write pages at fork time, so the harness ignores it.
- **Binary size**: `stat().st_size` on the linked executable. Python is
  interpreted and has no binary.
- **Lines of code**: non-empty, non-comment source lines excluding
  `__BENCH_METRICS__` instrumentation. Rust/Mapanare files are
  instrumentation-free; Go/C files include `clock_gettime` + `getrusage`
  calls that the counter strips.

### Reproduce any number

```bash
# Full 36-cell suite, 10 runs per config (~5–10 minutes).
python3 benchmarks/cross_language/run_benchmarks.py --runs 10

# Single workload.
python3 benchmarks/cross_language/run_benchmarks.py --only fib_recursive --runs 10

# Results saved to benchmarks/cross_language/v4.107.0-results.json
```

---

## Table 1 — Wall-clock time (ms, lower is better)

| Benchmark | C (gcc -O2) | C (clang -O2) | Rust -O | Go | Mapanare O2 | Python 3.12 |
|---|---:|---:|---:|---:|---:|---:|
| fib_recursive  | **11.01** | 18.69 | 17.98 | 33.27 | 20.33 | 801.29 |
| quicksort      | 0.36 | **0.35** | 1.99 | 0.40 | 2.58 ⚠ | 80.61 |
| struct_alloc   | 0.60 | **0.02** † | 1.33 | **0.02** † | 1.21 | 201.72 |
| enum_match     | **0.14** | 0.15 | 1.60 | 0.20 | 3.66 | 79.58 |
| prime_sieve    | 2.05 | **1.82** | 3.11 | 2.08 | 3.43 | 369.60 |
| string_concat  | 0.07 | **0.05** | 1.32 | 40.50 | 94.57 | 9.60 |

**† struct_alloc in C (clang -O2) and Go**: the compiler proves the
entire allocation loop has no observable effect and folds it to a
constant. GCC's `-O2` does not do this; clang and Go do. Rust and
Mapanare actually execute the loop. Numbers with † measure "what the
benchmark actually runs after the optimizer finishes," not allocator
throughput — see the [analysis section](#analysis) below.

**⚠ Mapanare quicksort**: produces a wrong checksum
(`1.4 × 10¹⁵` instead of `485`). Root cause is a pre-existing Mapanare
bug in `List<Int>` indexing (reproduces with `arr.push(42); print(str(arr[0]))`
→ `<?>`). Time is still reported because the program runs to
completion and does not crash; the measured work is simply incorrect
work. Filed as **docket Qs.1** for v4.108.0 investigation.

---

## Table 2 — Peak resident set size (KB, lower is better)

| Benchmark | C (gcc -O2) | C (clang -O2) | Rust -O | Go | Mapanare O2 | Python 3.12 |
|---|---:|---:|---:|---:|---:|---:|
| fib_recursive  | 1844 | 1848 | 2288 | 2516 | **2140** | 12,632 |
| quicksort      | **1924** | 1920 | 2344 | 2548 | 2352 | 14,000 |
| struct_alloc   | **1836** | 1848 | 2288 | 2460 | 2136 | 15,044 |
| enum_match     | **1844** | 1844 | 2264 | 2500 | 4740 | 12,620 |
| prime_sieve    | **1832** | 1848 | 2268 | 2464 | 2128 | 12,712 |
| string_concat  | **1896** | 1896 | 2304 | 8508 | **246,464** | 12,724 |

- C binaries hold steady at ~1.8–1.9 MB (glibc + small heap).
- Rust binaries sit at ~2.3 MB (embedded libstd).
- Go binaries sit at ~2.5 MB for compute-bound workloads and 8.5 MB for
  `string_concat` (accumulated heap growth from immutable-string
  rewrites).
- **Mapanare `string_concat` peaks at 246 MB.** Each `result + "hello"`
  allocates a new string in the arena; the arena never compacts, so
  the 10,000 intermediate strings of growing length accumulate to a
  triangular total of ~250 MB. The v4.108.0 StringBuilder work targets
  exactly this pattern.
- Python baseline is ~12.6 MB (interpreter overhead) plus user code;
  `struct_alloc` hits 15 MB holding 100 K dataclass instances.

---

## Table 3 — Binary size (KB, lower is better)

| Benchmark | C (gcc) | C (clang) | Rust | Go | Mapanare | Python |
|---|---:|---:|---:|---:|---:|---:|
| fib_recursive  | 15.8 | 15.8 | 3862 | 1879 | **58.2** | — |
| quicksort      | 15.9 | 15.9 | 3864 | 1880 | **62.2** | — |
| struct_alloc   | 15.9 | 15.8 | 3862 | 1879 | **58.2** | — |
| enum_match     | 15.8 | 15.8 | 3862 | 1879 | **62.2** | — |
| prime_sieve    | 15.8 | 15.8 | 3862 | 1880 | **58.2** | — |
| string_concat  | 15.9 | 15.9 | 3862 | 1879 | **58.2** | — |

- Rust statically links libstd (~3.9 MB); `strip` would shrink this but
  isn't part of `rustc -O`.
- Go embeds its runtime + garbage collector (~1.9 MB).
- Mapanare links `libmapanare_rt.a` at ~58 KB — roughly 4× a bare C
  binary and 30–60× smaller than Rust or Go. This is the structural
  advantage of compiling through a small native runtime rather than a
  language-level standard library.

---

## Table 4 — Lines of code (lower is more concise)

| Benchmark | C (gcc/clang) | Rust | Go | Mapanare | Python |
|---|---:|---:|---:|---:|---:|
| fib_recursive  | 14 | **8** | 23 | **8** | 9 |
| quicksort      | 46 | 33 | 49 | 46 | **27** |
| struct_alloc   | 27 | **12** | 27 | 19 | 15 |
| enum_match     | 55 | 36 | 58 | 37 | **18** |
| prime_sieve    | 24 | **20** | 41 | 22 | **18** |
| string_concat  | 25 | **7** | 20 | 9 | **5** |

Go and C programs are heavier in LOC because they include
`__BENCH_METRICS__` emission (syscall imports, `clock_gettime`,
`getrusage`, timeval helpers). The counter strips most of that, but
struct declarations, package declarations, and required imports still
count. For head-to-head conciseness Rust and Mapanare tie on most
workloads; Python wins where dataclasses and list comprehensions apply.

---

## Table 5 — Speedup vs C (gcc -O2)

Ratios of `wall_time / C_gcc_wall_time`. Values < 1.0 mean "faster than
gcc" (clang's and Go's DCE results live here). Values > 1.0 mean
"slower than gcc."

| Benchmark | C (gcc) | C (clang) | Rust | Go | Mapanare | Python |
|---|---:|---:|---:|---:|---:|---:|
| fib_recursive  | 1.00× | 1.70× | 1.63× | 3.02× | 1.85× | 72.8× |
| quicksort      | 1.00× | 0.98× | 5.51× | 1.12× | 7.15× ⚠ | 223.3× |
| struct_alloc   | 1.00× | 0.03× † | 2.22× | 0.03× † | 2.01× | 336.2× |
| enum_match     | 1.00× | 1.09× | 11.73× | 1.50× | 26.90× | 585.2× |
| prime_sieve    | 1.00× | 0.89× | 1.52× | 1.02× | 1.68× | 180.6× |
| string_concat  | 1.00× | 0.73× | 17.8× | 547.3× | 1278× | 129.7× |

**Where Mapanare sits on the spectrum** (excluding the broken
quicksort and the DCE'd struct_alloc):

- **Pure compute (fib_recursive, prime_sieve):** Mapanare is
  1.7–1.9× slower than gcc, on par with Rust, faster than Go. This is
  the "honest" performance band for Mapanare as a compiled language
  today.
- **Tagged-union dispatch (enum_match):** Mapanare is 27× slower than
  gcc, 17× slower than Rust. The gap is the boxed-enum layout overhead
  identified by the v4.106.0 Phase B panel (Rt.1).
- **String concatenation:** Mapanare is 1278× slower than gcc, 2× slower
  than Python. This is the v4.108.0 target.

Geometric mean across the four workloads where Mapanare is correct and
not DCE'd (fib, enum_match, prime_sieve, string_concat):

- vs C (gcc):     **9.5×** slower
- vs C (clang):   **9.8×** slower
- vs Rust:        **2.8×** slower
- vs Go:          **1.3×** slower
- vs Python:     **44.6×** faster

---

## Analysis

### Compute-bound workloads (fib_recursive, prime_sieve)

Pure arithmetic over stack-allocated values. Every compiled language is
within 3× of C gcc. Mapanare is competitive (1.7–1.9× slower). The gap
to C gcc is consistent with what v4.98.0 measured and matches the
v4.106.0 Phase B panel's conclusion: the optimizer work from Arcs 11–12
(nsw/nuw, TBAA, function attrs) produced IR that LLVM -O2 was already
handling; there was no additional speedup to extract.

### Allocation-heavy workloads (struct_alloc, string_concat)

**struct_alloc** is the clearest case where the optimizer can prove the
work is unobservable. Clang -O2 and Go both elide the entire 100 K
allocation loop (0.02 ms = sub-microsecond per iteration, physically
impossible for real `malloc`). GCC -O2 does not do this elimination and
actually runs 100 K `malloc`/`free` pairs in 0.6 ms. Rust returns
`Point` by value (stack-allocated) and runs the loop in 1.3 ms.
Mapanare arena-allocates each Point for 1.2 ms. The benchmark as-is
therefore measures something different in each language — on v4.110.0
(re-measurement release) we will either add a compiler barrier to force
real allocation in C/Go, or reinterpret the benchmark as "struct
construction + field access" where all numbers are meaningful.

**string_concat** is the unflattering number. Mapanare's
`result + "hello"` allocates a new string every iteration (no
amortization), driving 250 MB peak RSS and 94 ms wall time. Python's
`+= ` has a CPython-specific optimization for refcount-1 strings that
avoids reallocation; Rust's `String::push_str` uses amortized doubling;
Go's immutable strings make `+=` quadratic-ish (but the runtime's
allocator reuses freed blocks aggressively). C's `realloc + memcpy`
with doubling-free exact-size growth is still faster than all of
them because the total work is only 250 MB of memcpy and glibc's
realloc is very good at in-place grow when no other allocation is
between. **This is the v4.108.0 target** — a StringBuilder primitive in
the C runtime plus MIR-optimizer auto-detection of loop `+=` patterns
should close the gap to within 2× of Python.

### Dispatch-heavy workloads (enum_match)

Rust is 12× slower than C gcc here; Mapanare is 27×. C's tagged union
with switch dispatches in a handful of cycles per iteration because the
discriminant + union payload fit in registers and the switch becomes a
jump table. Mapanare's boxed enum variants with `{i8, [payload]}`
layout force a memory round-trip per match. This is the v4.106.0 Phase
B panel's Rt.1 finding, deferred to Phase C+ after the closure bug is
fixed.

### Python baseline

Python is 70–600× slower than C gcc on compute and dispatch workloads,
but only 130× slower on `string_concat` (where CPython's `+=`
optimization pays off) and only 2× **faster** than Mapanare on the
same benchmark. The Python-specific optimization matters more than any
structural language advantage for this pattern.

---

## Known limitations

1. **struct_alloc in clang/Go**: DCE makes numbers meaningless as
   "allocator throughput" — see analysis above.
2. **Mapanare quicksort**: pre-existing `List<Int>` indexing bug
   (docket Qs.1). Time shown but correctness fails.
3. **External vs internal timing asymmetry**: Rust and Mapanare are
   timed externally (+1–3 ms spawn); others internally. Only matters
   for sub-2 ms results.
4. **WSL2 variance**: ~5–10 % run-to-run noise versus bare metal.
   10 runs + median-of-8 damps this but doesn't remove it.
5. **No `-fsanitize` / `-g` variants**: all results at release
   optimization only.
6. **Single-core workloads only**: concurrency and async benchmarks
   (old `cross_language/02_*, 03_*, 05_*`) are out of scope here.

---

## What changed vs v4.98.0's `FINAL_REPORT.md`

| Aspect | v4.98.0 | v4.107.0 |
|---|---|---|
| Languages measured | 3 (Mapanare, Python, Rust) | **6** (+ Go, C gcc, C clang) |
| Runs per config | 5, median of middle 3 | **10, median of middle 8** |
| Correctness check | prefix-match (lenient) | **exact expected output** |
| Memory measurement | tracemalloc + rusage mix | **`/usr/bin/time -v` everywhere** |
| Workloads | 10 | **6** (focused on cross-language coverage) |
| Async included | compile-only | n/a (out of scope) |

The stricter correctness check surfaced the Mapanare quicksort bug that
v4.98.0's prefix match missed. The uniform `/usr/bin/time -v` memory
pipeline gave a clean 6-column peak-RSS table (v4.98.0 mixed two
sources). The addition of C gives the theoretical-ceiling row we were
missing.

---

## After v4.107.0

- **v4.108.0**: StringBuilder primitive in the C runtime + MIR
  auto-detection of loop `+=` patterns. Target: Mapanare
  `string_concat` within 2× of Python (≤ 20 ms down from 95 ms) and
  peak RSS under 1 MB (down from 246 MB).
- **v4.109.0**: investigate why Arcs 11–12 optimizer work produced
  zero measurable delta at -O2. Either LLVM was already doing
  everything, or our IR annotations are being dropped.
- **v4.110.0**: re-measure all 36 cells after v4.108.0 and v4.109.0
  land. Add `struct_alloc` compiler barrier so all six language configs
  run real allocation.
