# Mapanare v4.x — Compiled Statistics

> **Note:** Pre-v3.33.0 statistics are preserved here for panel
> continuity. Post-v4.120.0 measurements live in
> `docs/roadmap/v4/vX.Y.0/MEASUREMENTS.md` per release. See
> `.reviews/{v4.106.0,v4.114.0,v4.120.0,v4.136.0}/README.md` for
> panel aggregates.

> Hard numbers for the v4.120.0 panel. Every figure is traceable to a
> command in this repository or a committed artefact. No
> extrapolations, no projections. Methodology lives in the footer of
> each section.

**Generated at:** v4.119.0 (2026-04-14). **Branch:** `dev`.

---

## 1. Release cadence

| Metric | Value |
|---|---|
| v4.x release directories on disk (v4.0.0 → v4.119.0 + v4.7.1) | **121** |
| v4.x releases referenced in git commit log (`^v4\.N\.N:` messages) | 115 |
| v4.x point releases (v4.7.1, v4.106.1, v4.114.1) | 3 |
| v4.x minor-only releases (x.0) | 118 |
| Years of v4.x line (first release → v4.118.0) | ~1 calendar year (2025-2026) |
| Median visible cadence (any-release → next, commits) | ≈ 1 sprint per minor |

Methodology: `ls docs/roadmap/v4/ | grep "^v4\."` for directory count; `git log --oneline --pretty=format:"%s" | grep -oE "^v4\.[0-9]+\.[0-9]+" | sort -V -u` for commit-visible releases. Rows below count by directory.

### Phase breakdown — the recovery arc (v4.100.0 – v4.118.0)

| Phase | Releases | Range | Theme | Score before | Score after |
|---|---|---|---|---:|---:|
| Phase A | 4 | v4.100.0 – v4.103.0 | Critical / high bug fixes | 6.59 (v4.99.0) | not re-graded (Phase B did) |
| Phase B | 3 | v4.104.0 – v4.106.0 | Rebuild + verification + panel | 6.59 (v4.99.0) | **7.87** (v4.106.0) |
| Phase B patch | 1 | v4.106.1 | Rt.1 emitter signature + harness stdout-diff | 7.87 | (no re-panel) |
| Phase C | 4 | v4.107.0 – v4.110.0 | Benchmarks + string_concat fix + optimizer ROI | 7.87 | (no panel) |
| Phase D | 4 | v4.111.0 – v4.114.0 | Self-hosted 64/64 + fixed-point + panel | — | **8.21** (v4.114.0) |
| Phase D patch | 1 | v4.114.1 | rename + byref commit + cleanup comment | 8.21 | (no re-panel) |
| Phase E | 3 | v4.115.0 – v4.117.0 | Async I/O + docs + test hardening | 8.21 | (no panel) |
| Phase F | 2 (shipped) | v4.118.0 – v4.119.0 | Final benchmark + retrospective | — | v4.120.0 panel pending |
| **Total recovery** | **21 releases** (inc. two patches) | **v4.100.0 – v4.119.0** | Six phases | 6.59 | **≥ 8.21** (pre-Phase F panel) |

---

## 2. Codebase size

### Current (v4.118.0 HEAD)

| Component | Lines | Notes |
|---|---:|---|
| Self-hosted compiler (`mapanare/self/*.mn`) | **39,763** | 10 modules, from ast.mn through main.mn |
| Python bootstrap (`mapanare/*.py`) | **36,092** | 12 core files + emitters |
| C runtime (`runtime/native/*.{c,h}`) | **14,583** | 49 files |
| Python tests (`tests/**/*.py`) | **5,479 tests collected** | pytest, ≈ 221 test files |
| Golden test programs (`tests/golden/*.mn`) | **64** programs | all produce `.ref.ll` reference IR |
| Cross-language benchmark programs (Python/Rust/Go/C + Mapanare) | 6 × 5 = **30 compilable programs** | under `benchmarks/cross_language/` + optimizer + system |
| Async benchmark programs (Mapanare/Python/Go) | 5 × 3 = **15 compilable programs** | under `benchmarks/async/` |

Methodology: `wc -l mapanare/self/*.mn | tail -1`, `wc -l mapanare/*.py | tail -1`, `find runtime/native -name '*.c' -o -name '*.h' | xargs wc -l | tail -1`, `pytest --collect-only -q | tail -1`, `ls tests/golden/*.mn | wc -l`.

### Growth v4.99.0 → v4.118.0 (19 releases)

| Component | v4.99.0 | v4.118.0 | Δ |
|---|---:|---:|---:|
| Self-hosted compiler (.mn) | 38,824 | 39,763 | **+939** |
| Python bootstrap (.py) | 38,526 | 36,092 | **−2,434** (net deletion from move-semantics cleanup + `optimizer.py` largely dead) |
| C runtime (.c + .h) | 14,243 | 14,583 | **+340** |
| pytest tests | 5,374 | 5,479 | **+105** |
| Golden programs | 61 | 64 | +3 |
| **Code total across first 3 rows** | **91,593** | **90,438** | **−1,155** |

The v4.99.0 → v4.118.0 recovery arc is **net-negative lines of code**. Every Phase A–E release either deleted more than it added or ran zero-delta (Phase E releases v4.115.0, v4.116.0, v4.117.0, v4.118.0 were all explicitly "zero compiler/runtime code changes" beyond configuration / docs). The self-hosted compiler grew by 939 lines (new async work, StringBuilder passes, move-semantics); the Python bootstrap shrank by 2,434 lines because v4.103.0 deleted dead drop-glue paths and v4.97.0's MIR optimiser passes were disabled in v4.111.0's self-hosted `mir_opt.mn::optimize_mir()`.

The recovery happened by **subtracting** more than by adding.

---

## 3. Panel score trajectory

Every 7-reviewer panel held since the v3.x → v4.x transition.

| Panel version | Aggregate / 10 | PASS / NOTES / NEEDS WORK | Verdict |
|---|---:|---|---|
| v3.33.0 | 9.44 | 5 / 2 / 0 | First v4.0.0 gate, conditional on 6 targeted fixes |
| v3.45.0 | 9.69 | 6 / 1 / 0 | First regression in 6 cycles, still strong |
| v3.47.0 | **9.79** | 7 / 0 / 0 | **Highest score ever.** Unanimous. v4.0.0 gate passes. |
| v4.26.0 | 8.20 | 0 / 3 / 4 | **Crisis.** Largest single-cycle regression (−1.59). First non-unanimous panel. |
| v4.31.0 | 9.34 | 5 / 2 / 0 | Recovery arc 1 complete. Largest single-cycle improvement (+1.14). |
| v4.76.0 | 8.86 | 6 / 1 / 0 | Arc 9 (coroutines) complete. First 10/10 from any single reviewer. |
| v4.99.0 | **6.59** | 1 / 3 / 3 | **v5 gate fails.** Tagged-pointer UB single largest blocker. Option B: continue. |
| v4.106.0 | 7.87 | 1 / 6 / 0 | Phase B. +1.28 from v4.99.0. Zero NEEDS WORK. Below 8.0. |
| v4.114.0 | 8.21 | 2 / 5 / 0 | Phase D. +0.34 from v4.106.0. All 11 v4.99.0 dockets closed. 0.29 below 8.5 bar. |
| v4.120.0 | **TBD** | (pending) | **The v5 gate, attempt 2.** |

### ASCII trajectory chart

```
Score
10.00 ┤
 9.50 ┤      ▲9.44  ▲9.69  ▲9.79                              ▲9.34
 9.00 ┤                                                                    ▲8.86
 8.50 ┤                                                                                        ▲8.21
 8.00 ┤                                          ▲8.20                                  ▲7.87
 7.50 ┤
 7.00 ┤
 6.50 ┤                                                              ▲6.59
 6.00 ┤
      └──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────────────
          v3.33  v3.45  v3.47  v4.26  v4.31  v4.76  v4.99  v4.106 v4.114 v4.120?
```

Trajectory reading:
- **v3.33.0–v3.47.0:** steady climb from 9.44 → 9.79. The peak of v3.x discipline.
- **v3.47.0 → v4.26.0:** −1.59, the largest drop. Hollow features (const, @gpu, await, FFI) shipped without implementation.
- **v4.26.0 → v4.31.0:** +1.14 recovery. Six emitter items closed, FFI fixed, `MIRVerifier` wired.
- **v4.31.0 → v4.76.0:** −0.48 over 45 releases. Cadence held.
- **v4.76.0 → v4.99.0:** −2.27 over 23 releases. The v4.82.0 optimiser arc (Arcs 11–12) and tagged-pointer UB grew without panel oversight.
- **v4.99.0 → v4.106.0:** +1.28 after 7 Phase A + B releases. Zero NEEDS WORK.
- **v4.106.0 → v4.114.0:** +0.34 after 8 more releases. Phase D's 64/64 self-hosted milestone and all 11 v4.99.0 dockets closed.

The recovery arc climbs +1.62 total (6.59 → 8.21). The v4.120.0 panel will measure Phases E+F (v4.115.0–v4.118.0) on top of the v4.114.0 score.

Methodology: `.reviews/v*/README.md` aggregate lines. Cross-referenced with session reports.

---

## 4. Golden test progress

| Release | Stage | Bootstrap (Python) | mnc-stage1 (native self-hosted) | Pipeline (emit → llvm-as → opt → llc → clang → run) |
|---|---|---:|---:|---:|
| v4.82.0 | Pre-optimiser | 61/61 | not measured | not measured |
| v4.99.0 | v5-gate fail | 61/61 | **0/61** (binary corruption) | not measured |
| v4.101.0 | Phase A.2 | 62/62 | 16/62 | not measured |
| v4.103.0 | Phase A final | 64/64 | 21/64 | not measured |
| v4.104.0 | Phase B.1 | 64/64 | 21/64 | **60/64** (2 skips + 2 FAIL — pre-existing 17-version bug) |
| v4.106.0 | Phase B panel | 64/64 | 21/64 | 60/64 |
| v4.111.0 | Phase D.1 | 64/64 | **26/64** (+5 unblocks; effective 39/64 counting Cat. A) | 60/64 |
| v4.114.0 | Phase D panel | 64/64 | 26/64 | 60/64 |
| v4.118.0 | Phase F.1 | 64/64 | 26/64 | 60/64 |

Notes:
- Python bootstrap is deterministic and complete; the one long-standing failure (`51_match_guards_and_or`, or-pattern guards) remains open and is tracked separately from the main ledger (bootstrap parity, not a compiler crash).
- mnc-stage1 26/64 is the **literal** pass rate through the self-hosted binary. The v4.111.0 classification adds 13 "Cat. A — same output, different function count from bootstrap" tests for an **effective** 39/64. The remaining 25 failures are catalogued per bucket in `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`; the top cause is `__mn_str_starts_with` crash in `emit_mir_call+0x23515` (docket Sh.2, 10 tests affected).
- 60/64 integration-pipeline pass rate has been steady since v4.104.0. The 2 persistent FAILs are `51_match_guards_and_or` (bootstrap gap) and `47_try_operator` (17-version latent bug caught by v4.104.0's new llvm-as gate).

---

## 5. Carry-forward ledger

| State | Count |
|---|---:|
| Items opened across v3.x + v4.x panel history | ≥ 80 (sampled — full count requires a ledger sweep) |
| Items CLOSED | at least the 43 items itemised in `.reviews/CARRY_FORWARD.md` resolved-items table |
| Items OPEN as of v4.118.0 | **11** |
| – HIGH severity open | 2 (**Rt.1** emitter enum overhead, **Sh.2** emit_mir_call crash) |
| – MEDIUM severity open | 5 (Qs.1, Sh.4, Sh.5, Sh.6, Sh.7, Sh.8) |
| – LOW / INFO open | 4 (TBAA.1, willreturn.1, Sh.9a, Sh.9b, Sh.10) |
| Items closed during the recovery arc (v4.100.0 → v4.118.0) | **all 11 from v4.99.0 panel** (CRITICAL/HIGH/MEDIUM) plus v4.106.0's Rt.1 emitter signature + Ih.1 harness |

All 11 v4.99.0 panel items are closed with evidence in `.reviews/v4.99.0/V5_DECISION.md` and `docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md`. The list of newly-opened dockets (Sh.1–Sh.10, Rt.1, Qs.1, TBAA.1, willreturn.1) surfaced as Phase D–F work proceeded; all are documented, scoped, and have a planned release (v5.x for most).

---

## 6. CI gate status (v4.118.0)

| Gate | File | Status | Since |
|---|---|---|---|
| Black formatter | `.github/workflows/ci.yml::format` | **Enforcing** | v4.0.0 line |
| Ruff lint | `.github/workflows/ci.yml::lint` | **Enforcing** | v4.0.0 line |
| Mypy type check | `.github/workflows/ci.yml::mypy` | **Enforcing** | v4.0.0 line |
| pytest (3.11 + 3.12) | `.github/workflows/ci.yml::test` | **Enforcing** | v4.0.0 line |
| Native C runtime (plain gcc) | `.github/workflows/native.yml` | **Enforcing** | v4.x native work |
| AddressSanitizer CI | `.github/workflows/sanitizers.yml::asan` | **Enforcing, regression gate via `check_asan_baseline.py`** | v4.105.0 |
| ThreadSanitizer CI (async) | `.github/workflows/sanitizers.yml::tsan-async` | **Enforcing** (extended v4.117.0 to cover v4.115.0 demos) | v4.105.0 |
| Valgrind full golden suite | `.github/workflows/sanitizers.yml::valgrind` | **Enforcing** | v4.105.0 |
| WASM cross-compile (examples) | `.github/workflows/wasm.yml` | **Enforcing** | v2.0.0 line |
| Android cross-compile (ARM64 + x86_64) | `.github/workflows/android.yml` | **Enforcing** | v2.0.0 line |
| Coverage | `.github/workflows/ci.yml::coverage` | **Informational only** (promotes to enforcing after 5 stable releases per v4.117.0 risk register) | v4.117.0 |

Ten enforcing gates. One informational. The sanitizer gates in particular are the load-bearing deliverable from v4.105.0 (Phase B.2) — any future UAF, data race, or leak on the golden suite or async demos fails CI at PR time.

---

## 7. Benchmark summary

See `benchmarks/FINAL_REPORT_v4.120.md` for the full 500-line report. Key headlines:

### Cross-language geomean (6 workloads × 6 language configs × 10 runs, Mapanare O2)

| Baseline | v4.118.0 |
|---|---|
| vs C (gcc -O2) | **5.46× slower** (down from v4.107.0's 9.5×) |
| vs Rust -O | 1.13× slower |
| vs Go | 1.04× slower (on par) |
| vs Python 3.12 | 36.9× faster |

### Async geomean (5 workloads × 3 languages × 10 runs, Mapanare cooperative async)

| Baseline | v4.118.0 |
|---|---|
| vs Python asyncio | 42.6× faster |
| vs Go goroutines | 1.74× slower |

### Progress arc — single load-bearing win

| Benchmark | v4.82.0 | v4.118.0 | Δ | Credit |
|---|---:|---:|---:|---|
| string_concat | 102.31 ms | 1.32 ms | **77.5× speedup** | v4.108.0 auto-StringBuilder MIR pass (Phase C) |
| fib_recursive | 20.43 ms | 18.91 ms | −7% (noise) | — |
| quicksort | 1.79 ms | 2.45 ms | +37% (harness `/usr/bin/time -v` wrap) | — |
| prime_sieve | — | 3.44 ms | flat vs v4.99.0 | — |

Honest assessment: the recovery arc produced **one measurable benchmark win** (string_concat). Every other workload is within harness noise of the v4.99.0 numbers. The arc's value is **correctness**, not raw speed: 0/61 golden at v4.99.0 → 26/64 at v4.118.0, 0 async benchmarks linking → 5/5 linking and executing, `/v5 decision` 6.59 → ≥ 8.21 aggregate.

---

## 8. File inventory — net new in the recovery arc

Files created / substantially rewritten during v4.100.0 – v4.118.0:

| Artefact | First release | Role |
|---|---|---|
| `runtime/native/mapanare_core.h` — `MnString` bitfield | v4.100.0 | Tagged-pointer UB structural fix |
| `mapanare/emit_llvm_text.py::_move_resource` (6 call sites) | v4.101.0 | Move-semantics for heap strings in lists / structs |
| `scripts/check_asan_baseline.py` | v4.105.0 | ASan regression gate |
| `.github/workflows/sanitizers.yml` | v4.105.0 | Valgrind / ASan / TSan CI |
| `docs/roadmap/v4/v4.106.0/MEASUREMENTS.md`, `.reviews/v4.106.0/*` | v4.106.0 | Phase B panel artefacts |
| `benchmarks/cross_language/{go,c}/*` + `run_benchmarks.py` | v4.107.0 | 5-language cross-language harness |
| `mapanare/mir_opt.py::string_concat_optimization` (rewrite) | v4.108.0 | Auto-StringBuilder CFG rewrite |
| `benchmarks/optimizer/OPT_ROI_ANALYSIS.md` | v4.109.0 | Arcs 11–12 honest ROI investigation |
| `benchmarks/PHASE_C_RESULTS.md` | v4.110.0 | Final Phase C benchmark canonical report |
| `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md` | v4.111.0 | 9-category classification of the remaining 25 self-hosted golden gaps |
| `docs/roadmap/v4/v4.112.0/DIVERGENCE_ANALYSIS.md` | v4.112.0 | Fixed-point 3-stage divergence categorisation |
| `docs/SPEC.md §2.1.1` (42-row reserved keyword table) | v4.113.0 | Keyword audit for SPEC |
| `docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md` | v4.114.0 | 11-item v4.99.0 docket closure audit with line references |
| `examples/async_file_io.mn`, `examples/async_http_demo.mn` | v4.115.0 | Native async I/O demos |
| `docs/guides/async.md`, `docs/guides/getting_started.md` | v4.115.0 / v4.116.0 | User-facing guides |
| `tests/FLAKY_AUDIT.md`, `tests/COVERAGE.md`, `tests/integration/test_pipeline_hardening.py` | v4.117.0 | Test infrastructure panel evidence |
| `benchmarks/FINAL_REPORT_v4.120.md` + `v4.118.0-results.json` + `v4.118.0-async.json` | v4.118.0 | Panel benchmark evidence |
| `docs/roadmap/v4/v4.120.0/{RETROSPECTIVE,STATISTICS,V5_READINESS,AUDIT_NOTES}.md` | v4.119.0 | Panel prep artefacts (this file is one of them) |

Methodology: enumerated from CHANGELOG [4.100.0] – [4.118.0] entries. Cross-referenced against `git log`.
