# v4.107.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase C release 1 complete.** Six-column, six-workload
cross-language comparison table published as
`benchmarks/cross_language/FULL_COMPARISON.md`. Zero changes to the
Mapanare compiler, runtime, or `.mn` sources — pure measurement.
Discovered one pre-existing Mapanare bug (List<Int> indexing) that
the stricter v4.107.0 correctness checking surfaced; filed as docket
Qs.1 for v4.108.0+.

## Self-graded aggregate

**8.2 / 10**

- **Deliverable quality**: 6 Go + 6 C programs compile clean with both
  gcc and clang at `-O2 -Wall -Wextra -Wpedantic`, pass UBSan,
  produce correct checksums matching Python reference. Harness handles
  6 language configs uniformly with structured results in JSON.
  `FULL_COMPARISON.md` has 5 tables + methodology + analysis +
  reproducibility section. +strong
- **Honest measurement**: caught and fixed a subprocess-inherited-RSS
  bug in peak-memory reporting (programs' internal
  `getrusage(RUSAGE_SELF).ru_maxrss` was inflated by Python's COW
  pages at fork time — switched to `/usr/bin/time -v` wrapper for
  accurate per-process peak). Caught and documented the clang/Go
  DCE of `struct_alloc` rather than hiding it behind barriers.
  Caught and filed the Mapanare quicksort bug rather than loosening
  the correctness check. +strong
- **Scope discipline**: zero edits to `mapanare/`, `runtime/`, or any
  `.mn` source file. All new code is benchmark programs and harness
  glue under `benchmarks/cross_language/`. +strong
- **Documentation**: FULL_COMPARISON.md is readable, reproducible, and
  explicitly calls out every measurement caveat (external vs internal
  timing, DCE, subprocess memory inflation, WSL2 variance, Mapanare
  quicksort correctness failure). +solid
- **What's missing**: no v4.107.0-specific MEASUREMENTS.md beyond the
  final report; no Culebra integration (not needed — this release
  doesn't touch compiler/runtime code); geometric-mean numbers in the
  report are computed by hand rather than by the harness.

## What shipped

### Code
- `benchmarks/cross_language/go/` — 6 new Go programs (fib_recursive,
  quicksort, struct_alloc, enum_match, prime_sieve, string_concat).
  Each compiles with `go build`, emits `__BENCH_METRICS__` block via
  `clock_gettime(CLOCK_MONOTONIC)` + `syscall.Getrusage`, produces
  correct checksum matching Python reference. `go vet` clean.
- `benchmarks/cross_language/c/` — 6 new C programs. Each compiles
  clean with both `gcc -O2 -Wall -Wextra -Wpedantic` and
  `clang -O2 -Wall -Wextra -Wpedantic`. UBSan clean. Same metric
  emission pattern. `realloc + memcpy` for string_concat per the
  plan's Decision 2.
- `benchmarks/cross_language/run_benchmarks.py` — rewritten harness.
  6 language runners (Mapanare O2, Python, Rust, Go, C gcc, C clang).
  BENCHMARKS list is a registry of `BenchSpec` records mapping each
  workload to its 5 source file paths. `/usr/bin/time -v` wraps
  every run for accurate per-process peak RSS. Median of middle 8
  from 10 runs per config.

### Measurements
- `benchmarks/cross_language/v4.107.0-results.json` — raw 36-cell
  result set (6 workloads × 6 languages × 10 runs each, with
  per-run wall_time_s, cpu_time_s, peak_memory_kb, output, and
  aggregated medians).
- `benchmarks/cross_language/FULL_COMPARISON.md` — 5 tables
  (wall time, peak memory, binary size, LOC, speedup vs C gcc)
  + methodology, analysis, reproducibility, known limitations,
  "what changed vs v4.98.0" comparison.

### Headlines
- **Pure compute (fib, prime_sieve)**: Mapanare is 1.7–1.9× slower
  than C gcc, **on par with Rust**, faster than Go.
- **Tagged-union dispatch (enum_match)**: Mapanare is 27× slower
  than C gcc, 17× slower than Rust. Expected — the v4.106.0 Phase B
  panel's **Rt.1** boxed-enum overhead finding.
- **string_concat**: Mapanare is 1278× slower than C gcc, **2× slower
  than Python**. This is the v4.108.0 StringBuilder target.
- **Geometric mean** (across fib, enum_match, prime_sieve,
  string_concat — excluding DCE'd struct_alloc and broken quicksort):
  - 9.5× slower than C gcc
  - 2.8× slower than Rust
  - **1.3× slower than Go**
  - **44.6× faster than Python**

## Discovered during measurement

### Mapanare quicksort bug (docket Qs.1)

`benchmarks/optimizer/quicksort.mn` produces
`checksum = 1.4 × 10¹⁵` instead of the expected `485`. Non-deterministic
across runs, reproduces at O0/O1/O2. Root cause isolated to
`List<Int>` indexing:

```
pon mut arr: List<Int> = []
arr.push(42)
print(str(arr[0]))    // prints "<?>" instead of "42"
print("sum = " + str(arr[0] + arr[1] + arr[2]))  // prints garbage big number
```

`len(arr)` returns correctly (3 for 3 pushes), so the list count is
intact. Only the element accessor returns garbage. This is a
pre-existing bug — the v4.98.0 harness used a prefix-match correctness
check (`"checksum = "` with trailing space) that passed on any output
starting with that prefix, so the bug went unnoticed. v4.107.0's strict
exact-checksum check surfaced it.

Per v4.107.0 scope ("no code changes to Mapanare"), not fixed here.
Filed as docket **Qs.1** for v4.108.0 or the next compiler-work
release to investigate.

### Subprocess RSS inflation

`getrusage(RUSAGE_SELF).ru_maxrss` inside a subprocess.run-spawned
child is inflated by the Python parent's COW pages at fork time. A
tiny C "hello world" reports 12 MB peak when spawned from Python but
1.8 MB when run directly. Fix: always use `/usr/bin/time -v` which
uses `wait4()` after exec, giving post-exec peak only.

## What's next

- **v4.108.0** — StringBuilder primitive in `runtime/native/` + MIR
  optimizer auto-detection of loop `+=` patterns. Target: Mapanare
  string_concat under 20 ms (down from 95 ms) and peak RSS under
  1 MB (down from 246 MB). Re-run harness after landing to verify.
- **v4.109.0** — investigate zero optimizer delta from Arcs 11–12
  at -O2. Either LLVM was already doing everything, or annotations
  get dropped.
- **v4.110.0** — re-measure all 36 cells + add compiler barrier to
  struct_alloc so C (clang) and Go run real allocation.

## Phase C status

Phase C (benchmarks) is now **open**. v4.107.0 was release 1 of Phase
C — establish the cross-language comparison surface. v4.108.0 and
v4.109.0 close specific gaps the comparison revealed. v4.110.0
re-measures to confirm fixes landed.

## Commit trail

```
f4dafdf v4.107.0 phase 1: 6 Go benchmark programs
a7788ce v4.107.0 phase 2: 6 C benchmark programs (gcc -O2 + clang -O2 verified)
9d0ac0d v4.107.0 phase 3: harness updated for Go + C (gcc) + C (clang) targets
62ea7b7 v4.107.0 phase 4: full benchmark run -- 6 programs x 6 language configs
84aab98 v4.107.0 phase 5: FULL_COMPARISON.md published
        v4.107.0: Go + C added to cross-language benchmark suite  [final]
        Bump VERSION to 4.108.0                                   [follow-up]
```

## Exit criteria status

| # | Check | Status |
|---|---|---|
| 1 | 6 Go programs compile and produce correct output | ✅ all 6 correct checksums |
| 2 | 6 C programs compile with gcc and clang | ✅ both compilers, -Wall -Wextra -Wpedantic clean, UBSan clean |
| 3 | Harness runs Go + C (gcc) + C (clang) | ✅ 6 runners, 6 workloads, 36 cells |
| 4 | 36 entries in results JSON | ✅ `v4.107.0-results.json` has all 36 |
| 5 | Checksums match across languages | ⚠ 35/36 match; Mapanare quicksort is the one failure (pre-existing bug, docket Qs.1) |
| 6 | FULL_COMPARISON.md published with 5 tables | ✅ published |
| 7 | Numbers reproducible via documented commands | ✅ methodology section + reproduce command |
| 8 | 10 runs per config, median reported | ✅ 10 runs, median of middle 8 after dropping high/low |
| 9 | Standard closeout clean | ✅ ruff + black pass on touched files |

Exit criterion 5 is "match across languages for each benchmark" —
between C, Rust, Go, Python, and C (clang) all 6 benchmarks produce
identical checksums. Mapanare's quicksort discrepancy reflects a
Mapanare compiler bug, not a disagreement among the reference
implementations. Documented in FULL_COMPARISON.md and this report as
docket Qs.1 rather than a v4.107.0 scope violation.
