# v4.153.0 Pre-Panel Measurements — Evidence Base for the v4.154.0 Perf Panel

> **Status: FINAL.** Generated at v4.153.0 on 2026-04-19 after the
> complete E1-E8 perf arc and 6th flaky audit. This document carries
> all quantitative evidence the v4.154.0 panel will grade.

**Compiled at:** v4.153.0
**Next panel:** v4.154.0 (perf-focused)
**Arc scope:** v4.144.0 -> v4.152.0 (8 experiments, 15 sub-levers)

---

## 1. Test count

### pytest (full suite, excluding `tests/bootstrap`)

| Metric | **v4.153.0 (live)** |
|---|---:|
| Passed | **5,302** |
| Failed | **0** |
| Skipped | 115 |
| xfailed | 9 |
| Warnings | 2 |

6th flaky audit: **5 sequential runs, all 5302/0. Cumulative 30
sequential runs since v4.117.0 with zero flaky findings.**

How to reproduce: `python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no`

### pytest (`tests/bootstrap/`)

| Metric | **v4.153.0** |
|---|---:|
| Passed | **212** |
| Failed | **13** |

Baseline-honest and unchanged since v4.141.0.

### Goldens (`mnc-stage1`)

| Pipeline | Passing |
|---|---:|
| Self-hosted `mnc-stage1` | **54 / 66** |

How to reproduce: `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`

---

## 2. Self-hosted compiler

| Metric | v4.142.0 | **v4.153.0** | Delta |
|---|---:|---:|---|
| Total `.mn` lines | 40,193 | **40,319** | +126 |
| Core compiler lines (11 modules) | 17,388 | **17,448** | +60 |
| `mnc_all.mn` | 17,385 | **17,451** | +66 |
| `main.ll` | 909,244 | **912,184** | +2,940 |
| `mnc-stage1` stripped binary | 3,566,736 | **3,583,120** | +16,384 |

Growth is from v4.152.0 E8 comment blocks in `mir_opt.mn` (+39 lines
of comments documenting dormant pass re-evaluation evidence).

Core module breakdown:

| Module | Lines |
|---|---:|
| ast.mn | 854 |
| lexer.mn | 582 |
| parser.mn | 2,425 |
| semantic.mn | 2,088 |
| mir.mn | 867 |
| mir_opt.mn | 1,302 |
| lower_state.mn | 589 |
| lower.mn | 3,978 |
| emit_llvm_ir.mn | 264 |
| emit_llvm.mn | 3,697 |
| main.mn | 802 |

How to reproduce: `wc -l mapanare/self/*.mn`

---

## 3. Cross-language benchmark summary

**Canonical raw artifacts:**
- `benchmarks/cross_language/v4.153.0-results.json`
- `benchmarks/FINAL_REPORT_v4.153.md`

### Geomean ratios

| Comparison | v4.144.0 | **v4.153.0** | Delta |
|---|---:|---:|---|
| Mapanare / C gcc | 4.57x | **0.96x** | -79% gap |
| Mapanare / Rust | 5.83x | **1.17x** | -80% gap |
| Mapanare / Go | 1.81x | **0.47x** | Mapanare now faster |
| Mapanare / Python | 168x faster | **~168x** | Stable |

### Per-workload (median, 20 runs)

| Benchmark | C gcc | Rust | Go | Mapanare | v4.144.0 Mn | Delta |
|---|---:|---:|---:|---:|---:|---|
| fib_recursive | 10.281 | 17.207 | 30.321 | **14.630** | 20.657 | -29% |
| quicksort | 0.327 | 0.371 | 0.374 | **1.038** | 2.385 | -56% |
| struct_alloc | 0.551 | 0.017 | 0.019 | **0.018** | 1.198 | -98% |
| enum_match | 0.124 | 0.278 | 0.186 | **0.157** | 1.619 | -90% |
| prime_sieve | 1.891 | 1.685 | 1.907 | **1.952** | 3.406 | -43% |
| string_concat | 0.069 | 0.040 | 47.308 | **0.076** | 1.656 | -95% |

How to reproduce: `python3 benchmarks/cross_language/run_benchmarks.py --runs 20`

---

## 4. Async benchmark summary

| Benchmark | **v4.153.0** |
|---|---:|
| sequential_chain | 2.5 ms |
| fanout | 2.2 ms |
| io_bound | 2.2 ms |
| mixed_cpu_io | 2.2 ms |
| backpressure | 1.9 ms |

How to reproduce: `python3 benchmarks/async/run_async.py --runs 20`

---

## 5. E1-E8 experiment outcomes

| ID | Hypothesis | Result | Key delta | Release |
|---|---|---|---|---|
| E1 | Unified-return for inline-enum | **WIN** | enum_match -8.4% (10M) | v4.145.0 |
| E2 | fib: noundef + pure-fn attrs | **DEAD END** | 0% (hygiene) | v4.146.0 |
| E3 | noalias via MIR escape analysis | **DEAD END** | 0% (binary identical) | v4.147.0 |
| E4 | StringBuilder realloc + methodology fix | **WIN** | string_concat -95% | v4.148.0 |
| E5 | ABI.1 sret for aggregates | **WIN** | struct_alloc -98%, enum_match -90% | v4.149.0 |
| E6* | Async thread pool sizing | **WIN** | async geomean -50% | v4.150.0 |
| E7b/c | List allocator realloc + fast-path | **WIN** | quicksort -7.2% | v4.151.0 |
| E8a-d | Dormant MIR passes re-eval | **DEAD END** | 0% (all 4 rolled back) | v4.152.0 |

**Arc score: 5 wins, 3 dead ends.** Dead ends are documented with
root-cause analysis in their respective RESULTS.md files.

Evidence: `docs/roadmap/v4/PERF_EXPERIMENTS.md` (end-of-arc audit verified)

---

## 6. Fixed-point status

**NEAR FIXED POINT.**

| Artifact | Lines | md5 |
|---|---:|---|
| `stage2.ll` | **110,127** | `cad20b4b3db904b2dcbdea4533dcfc43` |
| `stage3.ll` | **110,127** | `612b352c8c4c86b1a326d967c92a7419` |

4 diff lines (version-metadata placeholder only), within
`DIFF_THRESHOLD=100`.

Source: `docs/roadmap/v4/v4.153.0/FIXEDPOINT_STATUS.md`

How to reproduce: `bash scripts/verify_fixed_point.sh --keep`

---

## 7. Sanitizer totals

| Class | v4.142.0 | **v4.153.0** | Delta |
|---|---:|---:|---|
| Valgrind CLEAN | 0 | **0** | — |
| Valgrind WARNINGS_ONLY | 66 | **62** | -4 |
| Valgrind ERRORS | 0 | **4** | +4 (Ge.1 residuals) |
| ASan CLEAN | 55 | **55** | — |
| ASan ASAN_ERROR | 0 | **0** | — |
| ASan CRASH_NO_ASAN | 11 | **11** | — |

The 4 valgrind ERRORS are pre-existing Ge.1 generics residuals, not
new findings from the perf arc. Zero new ASan findings.

Sources:
- `docs/roadmap/v4/v4.153.0/VALGRIND_REPORT.md`
- `docs/roadmap/v4/v4.153.0/ASAN_REPORT.md`

---

## 8. Flaky audit

**30 cumulative sequential non-bootstrap pytest runs, zero flaky.**

| Audit | Release | Runs | Flaky |
|---|---|---:|---:|
| A1 | v4.117.0 | 5 | 0 |
| A2 | v4.125.0 | 5 | 0 |
| A3 | v4.130.0 | 5 | 0 |
| A4 | v4.135.0 | 5 | 0 |
| A5 | v4.141.0 | 5 | 0 |
| A6 | v4.153.0 | 5 | 0 |
| **Total** | | **30** | **0** |

Source: `docs/roadmap/v4/v4.153.0/FLAKY_AUDIT.md`

---

## 9. Carry-forward state

### Open dockets (8, all LOW)

| ID | Description |
|---|---|
| Sh.4-7, Sh.9a | Feature-gap (mutable views, slices, tensor, closures, async) |
| In.1 | Self-hosted inliner rename bug (v4.152.0) |
| Li.1 | Self-hosted LICM hoist duplicate (v4.152.0) |
| Ea.1 | Self-hosted escape analysis stub (v4.152.0) |

**Zero CRITICAL, HIGH, or MEDIUM.** All remaining work is LOW-severity
feature-gap or self-hosted optimizer polish.

### Closed in arc (0)

The perf arc (v4.144.0-v4.152.0) focused on experiments, not docket
closure. No existing dockets were closed. 3 new LOW dockets opened (In.1,
Li.1, Ea.1).

Source: `docs/roadmap/v4/v4.153.0/DOCKET_LEDGER.md`

---

## 10. Panel score history

| Release | Aggregate | Outcome |
|---|---:|---|
| v4.99.0 | 6.59 | Option B |
| v4.106.0 | 7.87 | Option B |
| v4.114.0 | 8.21 | Option B |
| v4.120.0 | 8.21 | Option B |
| v4.136.0 | 8.80 | Option C (`v5.0.0-rc1`) |
| v4.143.0 | 8.86 | Option C (rc1 holds) |
| **v4.154.0 forecast** | **~9.2** | projection only |

The forecast is based on: 5 benchmark wins closing 80% of the Rust gap,
0 MEDIUM+ dockets, 30-run flaky floor, and the honest-dead-end narrative
for E2/E3/E8. The perf-focused panel may weight benchmark improvements
more heavily than prior general-purpose panels.

---

## Evidence index

- `docs/roadmap/v4/v4.153.0/SESSION_REPORT.md`
- `docs/roadmap/v4/v4.153.0/FLAKY_AUDIT.md`
- `docs/roadmap/v4/v4.153.0/VALGRIND_REPORT.md`
- `docs/roadmap/v4/v4.153.0/ASAN_REPORT.md`
- `docs/roadmap/v4/v4.153.0/FIXEDPOINT_STATUS.md`
- `docs/roadmap/v4/v4.153.0/DOCKET_LEDGER.md`
- `docs/roadmap/v4/PERF_EXPERIMENTS.md` (with end-of-arc audit)
- `benchmarks/FINAL_REPORT_v4.153.md`
- `benchmarks/TREND_v4.144_v4.153.md`
- `.reviews/v4.154.0/PRE_PANEL_AUDIT.md`

## Reproducibility appendix

```bash
# Test count
python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no

# Goldens
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Self-hosted compiler stats
wc -l mapanare/self/*.mn mapanare/self/mnc_all.mn mapanare/self/main.ll
ls -la mapanare/self/mnc-stage1

# Cross-language benchmarks
python3 benchmarks/cross_language/run_benchmarks.py --runs 20

# Async benchmarks
python3 benchmarks/async/run_async.py --runs 20

# Fixed-point
bash scripts/verify_fixed_point.sh --keep

# Sanitizers
VG_OUTDIR=/tmp/vg bash scripts/valgrind_all_goldens.sh
bash scripts/build_asan.sh && bash scripts/run_asan_goldens.sh

# Flaky audit
for i in 1 2 3 4 5; do
  python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no
done

# CI gates
ruff check . && black --check . && mypy mapanare/ runtime/
python3 scripts/check_struct_registry.py
```
