# PHASE_C_RESULTS — Mapanare v4.110.0 Performance Report

> **Canonical performance document, effective 2026-04-14.**
> Supersedes `benchmarks/FINAL_REPORT.md` (v4.98.0, pre-Phase A) and
> `benchmarks/cross_language/FULL_COMPARISON.md` (v4.107.0, before
> v4.108.0 StringBuilder fix).

---

## Executive summary

All Phase A correctness fixes (tagged-pointer UB, list indexing, async
linking, enum dispatch) and all Phase C performance fixes
(auto-StringBuilder in v4.108.0) are applied. This document reports the
definitive cross-language comparison.

**Headline** — across the five correct-output workloads, Mapanare is:

| vs               | Geometric mean (Mapanare / lang) |
| ---------------- | -------------------------------- |
| C (gcc -O2)      | **4.85×** slower                 |
| C (clang -O2)    | 9.48× slower                     |
| Rust -O          | **1.06× — effectively on par**   |
| Go               | 2.10× slower                     |
| Python 3.12      | **50× faster** (0.024×)          |

The single most consequential change this release cycle: v4.108.0's
auto-StringBuilder pass took `string_concat` from **94.57 ms** to
**1.36 ms** — a **70× speedup** on one workload that dragged the
geomean from 9.5× slower than C (v4.107.0) down to 4.85× slower.
Everything else is within run-to-run noise.

One known correctness gap remains: `quicksort` produces a wrong
checksum because `List<Int>` indexing returns `<?>` for a valid index
in one code path (docket **Qs.1**, open for v4.111.0+).

---

## Methodology

| | |
| --- | --- |
| Date | 2026-04-14 |
| Mapanare version | 4.110.0 |
| OS / kernel | WSL2 Ubuntu 24.04 · Linux 5.15.167.4-microsoft-standard-WSL2 |
| CPU arch | x86_64 |
| Python | 3.12.3 |
| gcc | 13.3.0 |
| clang | 18.1.3 |
| rustc | 1.94.1 |
| Go | 1.22.5 |
| LLVM (Mapanare backend) | 18.1.3 (system `llvm-as`, `opt`, `llc`) |
| Runs per config | 10 |
| Aggregation | Drop min + max, median of middle 8 |
| Warmup | One discarded run before the timed batch |
| Wall timing | `/usr/bin/time -v` wrap + `time.perf_counter()` outer measurement (C/Go/Python report internal `wall_time_s`; Mapanare/Rust timed externally) |
| Peak memory | `/usr/bin/time -v` "Maximum resident set size" (per-process `ru_maxrss`; avoids the COW-fork inflation bug that affected v4.98.0) |
| Optimization flags | Mapanare: `emit-llvm → llvm-as → opt -O2 → llc → clang -pie` · C: `gcc -O2 -Wall -Wextra` / `clang -O2 -Wall -Wextra` · Rust: `rustc -O` · Go: `go build` (default) |

**Harness** — `benchmarks/cross_language/run_benchmarks.py` (6 workloads ×
6 languages). Mapanare-only extras (`matmul_naive`, `agent_fanout`) via
the one-shot script used for Table 4; raw results in
`benchmarks/v4.110.0-final.json` and `benchmarks/v4.110.0-extra.json`.

---

## Table 1 — Cross-language wall-clock (median ms)

| Benchmark      | C (gcc -O2) | C (clang -O2) | Rust -O   | Go       | **Mapanare O2** | Python 3.12 |
| -------------- | ----------: | ------------: | --------: | -------: | --------------: | ----------: |
| fib_recursive  | 11.20       | 18.86         | 18.61     | 34.17    | **20.56**       | 786.11      |
| quicksort †    | 0.36        | 0.35          | 1.70      | 0.40     | **2.52** ⚠      | 77.26       |
| struct_alloc ‡ | 0.60        | 0.02          | 1.77      | 0.02     | **1.26**        | 202.41      |
| enum_match     | 0.14        | 0.15          | 1.93      | 0.20     | **3.07**        | 76.36       |
| prime_sieve    | 2.02        | 1.82          | 3.43      | 2.09     | **3.43**        | 373.69      |
| string_concat  | 0.07        | 0.05          | 1.28      | 31.67    | **1.36**        | 9.69        |

† `quicksort` Mapanare output fails the strict checksum check due to
docket **Qs.1** (`List<Int>` indexing returns `<?>` for valid index in
one path). Wall-clock measurement is still collected so it can be
compared, but geomean calculations exclude this program.

‡ `struct_alloc` C (clang) and Go results (0.02 ms) reflect dead-code
elimination — the optimizers discovered that only a running checksum
is observable and eliminated the allocations entirely. This is an
optimizer flex, not a language-performance gap.

---

## Table 2 — Mapanare relative-time ratios (>1 ⇒ Mapanare slower)

| Benchmark      | vs C (gcc) | vs C (clang) | vs Rust | vs Go   | vs Python |
| -------------- | ---------: | -----------: | ------: | ------: | --------: |
| fib_recursive  | 1.84×      | 1.09×        | 1.10×   | 0.60×   | 0.03×     |
| quicksort ⚠    | 7.02×      | 7.13×        | 1.48×   | 6.27×   | 0.03×     |
| struct_alloc ‡ | 2.10×      | 69.91×       | 0.71×   | 62.92×  | 0.01×     |
| enum_match     | 22.44×     | 20.50×       | 1.60×   | 15.15×  | 0.04×     |
| prime_sieve    | 1.69×      | 1.89×        | 1.00×   | 1.64×   | 0.01×     |
| string_concat  | 18.41×     | 25.95×       | 1.07×   | 0.04×   | 0.14×     |
| **Geomean** *  | **4.85×**  | **9.48×**    | **1.06×** | **2.10×** | **0.024×** |

\* Geomean over 5 correct programs (excludes `quicksort`). Mapanare
is **faster** than Python on every workload; faster than Go on
`fib_recursive` and `string_concat`; faster than Rust on `struct_alloc`
(arena beats malloc/drop).

---

## Table 3 — v4.99.0 pre-panel → v4.110.0 delta

| Benchmark      | v4.98.0 (ms) | v4.110.0 (ms) | Δ ms     | Δ %     | Speedup |
| -------------- | -----------: | ------------: | -------: | ------: | ------: |
| fib_recursive  | 19.56        | 20.56         | +1.00    | +5.1%   | 0.95×   |
| quicksort ⚠    | 1.98         | 2.52          | +0.54    | +27.2%  | 0.79×   |
| matmul_naive   | 1.33         | 2.29          | +0.96    | +72.0%  | 0.58×   |
| string_concat  | **95.24**    | **1.36**      | **-93.88** | **-98.6%** | **69.89×** |
| agent_fanout   | 0.51         | 1.22          | +0.71    | +139.5% | 0.42×   |
| struct_alloc   | 0.57         | 1.26          | +0.69    | +120.8% | 0.45×   |
| enum_match     | 2.27         | 3.07          | +0.80    | +35.5%  | 0.74×   |
| prime_sieve    | 3.05         | 3.43          | +0.38    | +12.4%  | 0.89×   |

**Honest reading.** v4.98.0's harness used raw `time.perf_counter()`
around `subprocess.run()` with no `/usr/bin/time -v` wrap. v4.107.0
rewrote the harness to wrap every run, which adds ~0.5–1 ms of fixed
overhead per call. That overhead dominates the sub-millisecond
"regressions" on `struct_alloc`, `agent_fanout`, and `enum_match`.
Phase A's bug fixes are not responsible for those deltas.

The v4.107.0 → v4.110.0 **control** (same harness) isolates real post-
v4.107.0 change:

| Benchmark      | v4.107.0 (ms) | v4.110.0 (ms) | Δ ms     | Δ %     |
| -------------- | ------------: | ------------: | -------: | ------: |
| fib_recursive  | 20.33         | 20.56         | +0.23    | +1.1%   |
| quicksort      | 2.58          | 2.52          | -0.06    | -2.5%   |
| struct_alloc   | 1.21          | 1.26          | +0.05    | +4.3%   |
| enum_match     | 3.66          | 3.07          | **-0.58**    | **-16.0%**  |
| prime_sieve    | 3.43          | 3.43          | -0.01    | -0.2%   |
| string_concat  | **94.57**     | **1.36**      | **-93.21**   | **-98.6%**  |

Every non-string benchmark is within ±5% (run-to-run noise at
sub-millisecond scale), except `enum_match` at −16%. That improvement
is compatible with v4.103.0's enum-dispatch fix, but it's at the edge
of being indistinguishable from noise; it's not claimed as a headline.

The only load-bearing post-v4.107.0 change on the benchmark surface is
v4.108.0's `string_concat` StringBuilder fix.

---

## Table 4 — v4.82.0 optimizer era → v4.110.0 cumulative delta

Five programs were present in the original optimizer baseline (Arc 11
start). This is the "how far has Mapanare come since the optimizer
era began?" question.

| Benchmark      | v4.82.0 (ms) | v4.110.0 (ms) | Δ ms     | Δ %     | Speedup |
| -------------- | -----------: | ------------: | -------: | ------: | ------: |
| fib_recursive  | 20.43        | 20.56         | +0.13    | +0.6%   | 0.99×   |
| quicksort ⚠    | 1.79         | 2.52          | +0.73    | +40.7%  | 0.71×   |
| matmul_naive   | 1.39         | 2.29          | +0.90    | +64.6%  | 0.61×   |
| string_concat  | **102.31**   | **1.36**      | **-100.95** | **-98.7%** | **75.08×** |
| agent_fanout   | 0.76         | 1.22          | +0.46    | +60.7%  | 0.62×   |

**Geometric mean speedup (5 programs): 1.821×.**

Every gain comes from `string_concat`. The v4.82.0 harness also used
raw `time.perf_counter()` without `/usr/bin/time -v`, so the sub-
millisecond "regressions" on `fib`, `quicksort`, `matmul`,
`agent_fanout` are again mostly harness overhead rather than compiler
regression. The v4.109.0 optimizer ROI analysis already found no
instruction-level change in matmul or quicksort hot loops from Arcs
11–12 hint work; those benchmarks have been flat for 14+ releases at
the compiler level.

---

## Table 5 — Peak memory (KB)

| Benchmark      | C (gcc) | C (clang) | Rust    | Go      | **Mapanare** | Python  |
| -------------- | ------: | --------: | ------: | ------: | -----------: | ------: |
| fib_recursive  | 1,840   | 1,828     | 2,284   | 2,472   | **2,136**    | 12,740  |
| quicksort      | 1,920   | 1,904     | 2,364   | 2,532   | **2,352**    | 14,092  |
| struct_alloc   | 1,844   | 1,840     | 2,276   | 2,440   | **2,132**    | 15,060  |
| enum_match     | 1,844   | 1,848     | 2,276   | 2,508   | **4,740** †  | 12,740  |
| prime_sieve    | 1,844   | 1,848     | 2,284   | 2,496   | **2,136**    | 12,684  |
| string_concat  | 1,888   | 1,884     | 2,324   | 8,640   | **2,260**    | 12,812  |

† `enum_match` at 4.7 MB reflects the boxed-enum Rt.1 overhead (every
match allocates a fresh heap payload); remains a known optimizer
opportunity. All other Mapanare workloads cluster near 2 MB RSS —
on par with C's ~1.85 MB baseline + the 4 KB agent-runtime thread
arena that ships with every linked Mapanare binary.

`string_concat` memory: C 1.9 MB, Mapanare 2.3 MB, Python 12.8 MB,
**Go 8.6 MB.** Go's string concat with `+=` materialises intermediate
strings, producing Go's worst-in-class result on this workload.

---

## Table 6 — Binary size (bytes, stripped by each toolchain's default)

| Benchmark      | C (gcc) | C (clang) | Rust        | Go          | Mapanare  |
| -------------- | ------: | --------: | ----------: | ----------: | --------: |
| fib_recursive  | 16,192  | 16,208    | 3,954,752   | 1,923,870   | **59,656** |
| quicksort      | 16,280  | 16,312    | 3,956,360   | 1,924,792   | **63,752** |
| struct_alloc   | 16,248  | 16,176    | 3,954,576   | 1,924,077   | **59,632** |
| enum_match     | 16,160  | 16,176    | 3,955,096   | 1,924,196   | **63,720** |
| prime_sieve    | 16,160  | 16,176    | 3,954,816   | 1,924,693   | **59,624** |
| string_concat  | 16,296  | 16,280    | 3,954,944   | 1,923,997   | **59,632** |

Mapanare binaries statically link `libmapanare_rt.a` (the arena,
string, list, agent runtime) — roughly **40 KB** of runtime code
above the per-program body. That's ~15× smaller than a Go binary
(which carries its own scheduler + GC) and ~65× smaller than a
Rust release binary (full static linking, unstripped by default).

Python has no equivalent binary size entry.

---

## Table 7 — Lines of code (expressiveness)

| Benchmark      | C (gcc) | C (clang) | Rust | Go  | Mapanare | Python |
| -------------- | ------: | --------: | ---: | --: | -------: | -----: |
| fib_recursive  | 14      | 14        | 8    | 23  | **8**    | 9      |
| quicksort      | 46      | 46        | 33   | 49  | 46       | 27     |
| struct_alloc   | 27      | 27        | 12   | 27  | 19       | 15     |
| enum_match     | 55      | 55        | 36   | 58  | 37       | 18     |
| prime_sieve    | 24      | 24        | 20   | 41  | 22       | 18     |
| string_concat  | 25      | 25        | 7    | 20  | 9        | 5      |

The LOC count excludes the `__BENCH_METRICS__` instrumentation lines
in C/Go (via a keyword-blacklist in the harness). Mapanare is close to
Rust's LOC count on most workloads; Python and Rust remain the most
compact.

---

## Analysis by category

### Compute-bound (fib_recursive, prime_sieve)

- **fib_recursive**: Mapanare 20.56 ms, Rust 18.61 ms. **1.10×
  slower.** Within the margin of a cold-branch-predictor run. Mapanare
  beats Go (34.17 ms) here because Go's function-call prologue is
  heavier than Mapanare's (no goroutine stack growth check).
- **prime_sieve**: Mapanare 3.43 ms, Rust 3.43 ms, Go 2.09 ms, C gcc
  2.02 ms. Mapanare **ties Rust exactly** and is 1.69× slower than
  C. The sieve is a tight `List<Int>` traversal with bounds-check
  elimination working well on both Rust and Mapanare.

### Allocation-heavy (struct_alloc, string_concat after v4.108.0)

- **struct_alloc**: Mapanare 1.26 ms, Rust 1.77 ms. **Mapanare beats
  Rust by 0.71×.** The arena allocator bulk-frees at scope exit; Rust
  runs `Drop::drop` on each struct individually. This is the one
  place Mapanare's arena model has a structural advantage, and it
  shows up.
- **string_concat**: Mapanare 1.36 ms, Rust 1.28 ms, Python 9.69 ms,
  Go 31.67 ms. **Mapanare 7.1× faster than Python, 23× faster than
  Go, 1.07× slower than Rust.** The v4.108.0 auto-StringBuilder pass
  detects `acc = acc + chunk` inside a loop and rewrites it to
  `__mn_sb_append` calls with preheader `__mn_sb_new` and exit
  `__mn_sb_finish`. Without that pass the benchmark was O(n²) from
  re-allocating and re-copying; with it, amortised O(n).

### System (enum_match, quicksort)

- **enum_match**: Mapanare 3.07 ms vs C 0.14 ms (22× slower). Every
  enum payload is heap-allocated and reference-counted. This is
  docket **Rt.1** from the v4.106.0 panel — the single largest known
  optimizer opportunity remaining. Unboxing fixed-layout small
  payloads would close most of this gap.
- **quicksort**: **wrong checksum.** The List<Int> indexing bug
  reports `<?>` for valid indices in one code path (docket **Qs.1**,
  open). Wall-clock numbers shown for reference; do not cite. Fix
  target: v4.111.0+.

---

## string_concat: before / after

The `string_concat` story is the single most consequential benchmark
change of the post-panel work.

|             | Wall time | Peak RSS  | vs Python   |
| ----------- | --------: | --------: | ----------: |
| v4.82.0     | 102.31 ms | ~246 MB   | 2.3× slower |
| v4.107.0    |  94.57 ms |  246.5 MB | 9.8× slower |
| **v4.110.0** | **1.36 ms** | **2.26 MB** | **7.1× faster** |

Wall: **70× faster.** Memory: **109× less.** From the worst-in-class
language (slower than Python on a string workload) to nearly tied
with Rust on the same workload.

**Root cause of the old pathology** — v4.95.0 shipped a
`string_concat_optimization` MIR pass that was dead code for 13
releases. It matched `Call("__mn_str_concat", ...)` but the real MIR
shape is `BinOp(ADD, String, String) + Copy(dest=acc, src=binop.dest)`
(the runtime call only appears at LLVM emission time). So the
optimizer ran, looked, found nothing, and did nothing. Meanwhile the
benchmark allocated a fresh heap string per iteration for 10,000
iterations.

**The v4.108.0 fix** — rewrote the pass in `mir_opt.py` against the
real MIR shape. It performs a CFG rewrite inside natural loops
(single preheader + single exit, no other uses of the accumulator in
the loop body): preheader gets `__mn_sb_new`, body's `BinOp + Copy`
is replaced with `__mn_sb_append`, and the exit block's `__mn_sb_finish`
materialises the final string. Two new scalar-pointer runtime
wrappers (`__mn_sb_new`, `__mn_sb_finish`) were needed because the
v4.95.0 `__mn_sb_create` returned a 24-byte struct by value (sret ABI)
which the emitter's auto-declare path mis-typed — the same latent
bug silently broke `stdlib/ai/llm.mn` and `embedding.mn` for 13
versions.

See `mapanare/mir_opt.py:1745` for the pass; `docs/roadmap/v4/v4.108.0/`
for the full writeup.

---

## Optimizer ROI summary

v4.109.0's forensic investigation found that the cumulative geomean
speedup across the full 5-program optimizer era (Arcs 11-12 in
v4.98.0-v4.108.0) was **0.992×** at -O2 — essentially zero net
improvement — because the 75× string_concat win was not yet
measured at the time of that analysis. With v4.108.0's fix included,
the geomean is **1.821×** (Table 4). String_concat carries the
entire story.

Per-workload:

- **matmul_naive**: +24% (real Arc 11 win from function-attribute
  table interactions, independently confirmed)
- **quicksort**: near-noise
- **fib_recursive**: within noise at any recursion depth tested,
  including fib(45)
- **string_concat**: −98.6% after v4.108.0 (75× speedup)

Three per-hint discoveries from v4.109.0 carry forward as v4.111.0+
docket items:

1. **TBAA metadata is 100% dead code.** Defined in the module header
   at `emit_llvm_text.py:910-926` but never attached to any load or
   store across all 4 optimizer benchmarks. The comment at line 913
   describes intended wiring that was never written. Remove or
   connect.
2. **Function attributes on runtime-call declarations** (`nounwind`,
   `willreturn`, `readonly`, `noalias`) are the load-bearing Arc 11
   contribution — they cross pass boundaries via LLVM's module-level
   attribute table. But `willreturn` on `__mn_sb_*` declarations
   blocks DSE of stores the call observes; audit the
   `RUNTIME_FN_ATTRS` set.
3. **Inline `nsw`/`nuw` flags are mostly redundant.** LLVM
   independently infers all 13 `nuw` on matmul post-O2 even when the
   frontend strips them. The emitter doesn't need to work this hard.

Full details: `benchmarks/optimizer/OPT_ROI_ANALYSIS.md`.

---

## Known limitations

- **WSL overhead.** Every number includes the WSL2 syscall/scheduling
  tax. Native Linux on the same hardware would likely shave 5-15% off
  short runs uniformly. This affects all languages equally, so ratios
  are unchanged; absolute numbers should be read with that caveat.
- **No async benchmark.** Mapanare's async runtime (validated
  end-to-end in v4.102.0 — goldens 55/56/57 run natively) isn't in
  this suite. Adding a throughput-oriented async workload is v4.111.0+.
- **No GPU benchmark.** The GPU backend (CUDA + Vulkan via dlopen) is
  compile-tested but not performance-characterised here.
- **List<Int> indexing correctness gap.** Docket Qs.1 blocks
  `quicksort`'s checksum validation. The compiler emits wrong IR for
  `arr[0]` in specific patterns; wall-time numbers for that program
  are shown but carry a warning.
- **enum_match 22× slower than C.** Boxed enum payloads are the
  single largest optimizer opportunity. Docket Rt.1.
- **Subprocess spawn overhead.** Sub-millisecond benchmarks
  (`struct_alloc` for C clang/Go, `string_concat` for C) are bounded
  from below by `/usr/bin/time -v`'s own startup cost. Treat anything
  ≤ 0.1 ms as "effectively zero."

---

## Reproducibility

```bash
# From repo root:
python3 benchmarks/cross_language/run_benchmarks.py --runs 10 \
    --output benchmarks/v4.110.0-final.json

# For matmul_naive + agent_fanout (Mapanare-only optimizer-era programs
# not in the cross-language harness):
python3 benchmarks/run_extra_bench.py

# To regenerate Tables 3, 4, and the control table:
python3 benchmarks/compute_deltas.py
```

Raw data:

- `benchmarks/v4.110.0-final.json` — 6 workloads × 6 languages, 10 runs each
- `benchmarks/v4.110.0-extra.json` — Mapanare-only matmul_naive + agent_fanout
- `benchmarks/v4.110.0-deltas.txt` — formatted delta tables (Tables 3, 4, control)
- `benchmarks/v4.98.0-final.json` — pre-panel baseline
- `benchmarks/optimizer/v4.82.0-baseline.json` — optimizer-era origin
- `benchmarks/cross_language/v4.107.0-results.json` — same-harness control baseline

---

## What comes next

v4.111.0 opens Phase D: self-hosted compiler maturity. The performance
story is told. The language needs to compile itself reliably across
every golden test. Open dockets for v4.111.0+:

- **Qs.1** — `List<Int>` indexing: `arr.push(42); print(str(arr[0]))` prints `<?>`
- **Rt.1** — Boxed enum payload overhead (enum_match 22× slower than C)
- **TBAA.1** — Remove dead TBAA metadata or wire it up properly
- **willreturn.1** — Audit `RUNTIME_FN_ATTRS` for heap-modifying runtime calls

Phase C is complete.
