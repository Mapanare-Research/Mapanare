# Mapanare v4.118.0 — Final Cross-Language Benchmark

> **Phase F release 1.** All fixes from Phase A (critical bugs), Phase B
> (rebuild + verification), Phase C (Go + C benchmarks, string fix),
> Phase D (64/64 self-hosted, fixed-point, medium items), and Phase E
> (async I/O, documentation, test hardening) have landed. This is the
> final honest measurement: 6 benchmarks, 5 languages, 10 runs each.
> No code changes. No optimizations. Pure measurement of where
> Mapanare stands after 20 recovery releases.

**Status:** DONE (shipped 2026-04-14)
**Breaking:** No
**Prerequisite:** v4.117.0
**Delta review:** No
**Full panel:** No (v4.120.0)
**Estimated work:** 1 sprint
**Theme:** Measure everything. Publish the definitive "where does Mapanare stand" document.

## Result

All 8 exit criteria met. Geomean across 6 workloads: **5.46× slower
than C gcc -O2** (down from 9.5× at v4.107.0), **1.13× slower than
Rust**, **on par with Go**, **36.9× faster than Python 3.12**. Async
geomean across 5 workloads: **42.6× faster than Python asyncio**,
**1.74× slower than Go goroutines**. `string_concat` progress
v4.82.0 → v4.118.0: **102.31 ms → 1.32 ms (77.5× speedup)**, Phase C
(v4.108.0) credit. See `SESSION_REPORT.md` and
`benchmarks/FINAL_REPORT_v4.120.md`.

---

## Scope

The v4.107.0 `FULL_COMPARISON.md` established the 5-language benchmark suite: C (gcc -O2), C (clang -O2), Rust (-O), Go, Mapanare (mnc-stage1 + opt -O2), Python 3.12. Since then, Phase A fixed the tagged-pointer UB that was causing string corruption, Phase C fixed the string_concat performance regression, Phase D completed the self-hosted compiler at 64/64, and Phase E hardened the test suite.

v4.118.0 re-runs every benchmark from v4.107.0 plus any new benchmarks that became possible (async, if Go comparison is available). The result is a three-column progress table: v4.82.0 (original baseline) -> v4.99.0 (pre-fix) -> v4.118.0 (current). This table tells the full story of the recovery arc.

The final report (`benchmarks/FINAL_REPORT_v4.120.md`) is the definitive document the v4.120.0 panel will reference. It must be reproducible, honest, and complete.

## Phase 1 -- Run ALL benchmarks

- [ ] Verify benchmark programs are current and unmodified since v4.107.0
- [ ] Run full suite: `python benchmarks/cross_language/run_benchmarks.py --runs 10`
- [ ] Targets: Mapanare (mnc-stage1 + opt -O2), Python 3.12, Go, Rust (-O), C (gcc -O2), C (clang -O2)
- [ ] Record per-benchmark, per-language: median wall time (ms), median peak memory (KB), binary size (KB)
- [ ] Report median of middle 8 runs (drop highest and lowest)
- [ ] Standard deviation for each measurement
- [ ] Save raw results to `benchmarks/cross_language/v4.118.0-results.json`
- [ ] Verify correctness: all programs produce expected checksums

## Phase 2 -- Async benchmarks (if available)

- [ ] Check if async benchmark programs exist from v4.115.0
- [ ] If Go async comparison is available (goroutines vs Mapanare async):
  - Run async file I/O benchmark: Go vs Mapanare, 10 runs each
  - Run async TCP benchmark: Go vs Mapanare, 10 runs each
  - Record same metrics: wall time, peak memory
- [ ] If async benchmarks are not comparable across languages, document why

## Phase 3 -- Progress table

- [ ] Collect v4.82.0 baseline numbers (from `benchmarks/cross_language/v4.82.0-results.json` or equivalent)
- [ ] Collect v4.99.0 numbers (from `benchmarks/cross_language/v4.99.0-results.json` or equivalent)
- [ ] Compute progress table:
  ```
  | Benchmark     | v4.82.0 (ms) | v4.99.0 (ms) | v4.118.0 (ms) | Delta 82->118 |
  |---------------|--------------|--------------|---------------|---------------|
  | fib_recursive | ...          | ...          | ...           | ...           |
  | quicksort     | ...          | ...          | ...           | ...           |
  | struct_alloc  | ...          | ...          | ...           | ...           |
  | enum_match    | ...          | ...          | ...           | ...           |
  | prime_sieve   | ...          | ...          | ...           | ...           |
  | string_concat | ...          | ...          | ...           | ...           |
  ```
- [ ] Compute per-benchmark improvement percentage
- [ ] Identify which phase contributed each improvement (Phase A string fix, Phase C optimizer, etc.)

## Phase 4 -- FINAL_REPORT

- [ ] Write `benchmarks/FINAL_REPORT_v4.120.md`:
  - **Methodology**: hardware specs, OS, compiler versions (gcc, clang, go, rustc, python, LLVM), run count, median method, environment controls
  - **Table 1: Wall-clock time (ms)** -- all 6 benchmarks x 5 languages (+ 2 C compiler variants)
  - **Table 2: Peak memory (KB)** -- same dimensions
  - **Table 3: Binary size (KB)** -- compiled languages only
  - **Table 4: Lines of code** -- all 6 languages, all 6 benchmarks (expressiveness comparison)
  - **Table 5: Speedup vs C (gcc -O2)** -- ratio for each language relative to the theoretical ceiling
  - **Table 6: Progress** -- v4.82.0 -> v4.99.0 -> v4.118.0 for Mapanare only
  - **Analysis**: where Mapanare sits on the C -> Rust -> Go -> Mapanare -> Python spectrum per workload category
  - **Reproducibility**: exact commands to reproduce every number
- [ ] Cross-reference with v4.107.0 `FULL_COMPARISON.md` -- note any changes

## Phase 5 -- ASCII position chart

- [ ] Generate an ASCII chart showing Mapanare's position on the performance spectrum:
  ```
  C (gcc)  C (clang)  Rust    Go    Mapanare    Python
  |--------|----------|-------|-----|-----------|----->
  1.0x     1.02x      1.1x   2.3x  ???x        50x
  ```
- [ ] One chart per benchmark category (compute, memory, string)
- [ ] Include in the FINAL_REPORT

## Phase 6 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.118.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | All 6 benchmarks run on all 5 language configs (+ 2 C variants) | `v4.118.0-results.json` |
| 2 | 10 runs per config, median + stddev reported | JSON run count |
| 3 | Checksums match across languages | harness output |
| 4 | Progress table computed: v4.82.0 -> v4.99.0 -> v4.118.0 | table in FINAL_REPORT |
| 5 | `FINAL_REPORT_v4.120.md` published with all tables | file exists |
| 6 | Methodology documented for reproducibility | methodology section |
| 7 | ASCII position charts generated | charts in FINAL_REPORT |
| 8 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Optimize Mapanare** -- zero compiler or runtime changes. Pure measurement. If numbers are bad, they are reported honestly.
- **Change benchmark programs** -- the programs from v4.107.0 are used as-is. No tuning for any language.
- **Run a panel** -- this release produces data. The panel at v4.120.0 interprets it.
- **Compare debug vs release** -- all compiled languages measured at standard release optimization only.
- **Add new benchmark workloads** -- the 6 workloads from v4.107.0 are the fixed set.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Numbers are worse than v4.107.0 due to Phase A/D code changes | low | medium | Report honestly. The panel evaluates the full picture, not just benchmarks. |
| string_concat is still slow despite Phase C fix | medium | medium | Report the number. The Phase C fix targeted correctness, not necessarily performance. |
| Missing baseline data from v4.82.0 or v4.99.0 | low | medium | Use whatever historical data is available. Note any gaps in the methodology section. |
| Go or Rust toolchain version changed since v4.107.0, invalidating comparison | low | low | Document all tool versions. If changed, note it. |
| Benchmark variance too high for meaningful comparison | low | medium | 10 runs with outlier removal (middle 8) handles this. Sub-1ms results reported as "below measurement threshold." |

---

## After v4.118.0

v4.119.0 writes the retrospective: the full journey from v4.0.0 to v4.120.0, statistics, v5 readiness assessment, and pre-panel audit. v4.120.0 is the panel -- 7 reviewers, the v5 gate (attempt 2). The FINAL_REPORT from this release is the benchmark evidence the panel will reference.
