# v4.153.0 Session Report

**Date:** 2026-04-19
**Theme:** Pre-perf-panel refresh
**Result:** Zero code changes. All evidence artifacts for v4.154.0 panel generated.

## What was done

Measurement-only release preparing the quantitative evidence base for
the v4.154.0 perf panel. Mirrors v4.135.0 (pre-v4.136.0 panel) and
v4.142.0 (pre-v4.143.0 panel) discipline.

### 6th flaky audit (A6)

5 sequential non-bootstrap pytest runs, all **5302 passed / 0 failed**.
Cumulative: **30 sequential runs across 6 audits, zero flaky findings.**
Anaconda score floor confirmed.

### Sanitizer sweeps

- **Valgrind**: 0/62/4 (4 ERRORS are pre-existing Ge.1 residuals)
- **ASan**: 55/0/11 (zero ASan errors; 11 CRASH_NO_ASAN are feature-gap tests)

### Cross-language benchmarks (20 runs per cell)

| Benchmark | Mapanare | vs Rust | vs v4.144.0 |
|---|---:|---:|---|
| fib_recursive | 14.630 ms | 0.85x | -29% |
| quicksort | 1.038 ms | 2.80x | -56% |
| struct_alloc | 0.018 ms | 1.06x | -98% |
| enum_match | 0.157 ms | 0.56x | -90% |
| prime_sieve | 1.952 ms | 1.16x | -43% |
| string_concat | 0.076 ms | 1.90x | -95% |
| **geomean** | — | **1.17x** | **-80% gap** |

### Fixed-point

NEAR FIXED POINT. 110,127 lines, 4 diff (version placeholder only).

### PERF_EXPERIMENTS.md end-of-arc audit

All 15 sub-levers verified against live file:line references. 0 cosmetic
drift, 0 material discrepancies.

### Pre-panel audit

42/42 load-bearing claims across 8 SESSION_REPORTs (v4.145.0-v4.152.0)
verified against HEAD. 0 material discrepancies.

## Artifacts produced

| Artifact | Location |
|---|---|
| FLAKY_AUDIT.md | `docs/roadmap/v4/v4.153.0/` |
| VALGRIND_REPORT.md | `docs/roadmap/v4/v4.153.0/` |
| ASAN_REPORT.md | `docs/roadmap/v4/v4.153.0/` |
| FIXEDPOINT_STATUS.md | `docs/roadmap/v4/v4.153.0/` |
| DOCKET_LEDGER.md | `docs/roadmap/v4/v4.153.0/` |
| MEASUREMENTS.md | `docs/roadmap/v4/v4.153.0/` |
| FINAL_REPORT_v4.153.md | `benchmarks/` |
| TREND_v4.144_v4.153.md | `benchmarks/` |
| PRE_PANEL_AUDIT.md | `.reviews/v4.154.0/` |
| v4.153.0-results.json | `benchmarks/cross_language/` |
| v4.153.0-async.json | `benchmarks/async/` |
| Flaky run logs (5) | `docs/roadmap/v4/v4.153.0/flaky-runs/` |
| valgrind-summary.tsv | `docs/roadmap/v4/v4.153.0/` |
| asan-summary.tsv | `docs/roadmap/v4/v4.153.0/` |
| goldens.log | `docs/roadmap/v4/v4.153.0/` |
| fixedpoint.log | `docs/roadmap/v4/v4.153.0/` |

## Code changes

**None.** Only files changed are:
- `VERSION` (4.152.0 -> 4.153.0)
- `README.md` (benchmark numbers + test badge)
- `CLAUDE.md` (v4.153.0 entry)
- `ROADMAP.md` (v4.153.0 section)
- `CHANGELOG.md` (v4.153.0 entry)
- `PERF_EXPERIMENTS.md` (end-of-arc audit overlay)
- Rebuilt `libmapanare_rt.a`, `mnc-stage1`, `main.ll` (VERSION embed)

## Verification

- `ruff check .` — clean
- `black --check .` — 353 unchanged
- `mypy mapanare/ runtime/` — 0 issues
- `check_struct_registry.py` — clean (23/23/89)
- Goldens — 54/66
- Fixed-point — NEAR (4 diff)
- Pytest — 5302 / 0 (5 runs, identical)
- Valgrind — 0/62/4
- ASan — 55/0/11

## What's next

**v4.154.0 — THE PERF PANEL.** 7-reviewer panel grading v4.144.0 ->
v4.153.0. Every number on the panel desk comes from this release.
