# v4.142.0 Pre-Panel Measurements — Evidence Base for the v4.143.0 Panel

> **Status: FINAL.** Generated at v4.142.0 on 2026-04-16 after Ge.1
> closure and the full evidence refresh. This document carries the
> v4.135.0 panel evidence base forward through the v4.137.0–v4.142.0
> bridge releases.

**Compiled at:** v4.142.0
**Next panel:** v4.143.0

---

## 1. Test count

### pytest (full suite, excluding `tests/bootstrap`)

| Metric | **v4.142.0 (live)** |
|---|---:|
| Passed | **5160** |
| Failed | **0** |
| Skipped | 115 |
| xfailed | 9 |
| Warnings | 2 |
| Wall time | 403.22 s |

The first verification attempt surfaced one deterministic VERSION-sync
failure in `tests/runtime/test_user_agent.py`; rebuilding
`libmapanare_rt.a` for `4.142.0` cleared it, and the rerun finished
clean.

### pytest (`tests/bootstrap/`)

| Metric | **v4.142.0 (live)** |
|---|---:|
| Passed | **212** |
| Failed | **13** |

Baseline-honest and unchanged in class from the v4.141.0 line.

### Goldens (`mnc-stage1`)

| Pipeline | Passing |
|---|---:|
| Self-hosted `mnc-stage1` | **54 / 66** |

The prompt's historical `65`-test count is now stale; the live corpus is
**66** after `66_qualified_type_ref.mn`.

---

## 2. Self-hosted compiler

| Metric | Value |
|---|---:|
| Total `.mn` lines in `mapanare/self/*.mn` | **40,193** |
| Core compiler lines (11 modules) | **17,388** |
| `mnc_all.mn` | **17,385** lines |
| `main.ll` | **909,244** lines |
| `mnc-stage1` stripped binary | **3,566,736 bytes** |

Core module breakdown:

- `ast.mn` 854
- `lexer.mn` 582
- `parser.mn` 2,425
- `semantic.mn` 2,077
- `mir.mn` 867
- `mir_opt.mn` 1,263
- `lower_state.mn` 589
- `lower.mn` 3,974
- `emit_llvm_ir.mn` 264
- `emit_llvm.mn` 3,691
- `main.mn` 802

---

## 3. Benchmark refresh

**Canonical raw artifacts:**

- `benchmarks/cross_language/v4.142.0-results.json`
- `benchmarks/async/v4.142.0-async.json`
- `benchmarks/FINAL_REPORT_v4.143.md`

The benchmark runners were re-issued with `--output` so the `.json`
artifacts are actual JSON. Shell redirection alone is insufficient with
the current harness.

### Cross-language geomean

| Language | Geomean |
|---|---:|
| C gcc | 0.533 ms |
| C clang | 0.301 ms |
| Rust | 11.769 ms |
| Go | 1.058 ms |
| **Mapanare** | **5.841 ms** |
| Python | 108.338 ms |

Relative readout:

- **10.96× slower than C gcc**
- **19.43× slower than C clang**
- **5.52× slower than Go**
- **0.50× of Rust** (about **2.0× faster**)
- **18.55× faster than Python**

### Async geomean

| Language | Geomean |
|---|---:|
| **Mapanare** | **5.817 ms** |
| Python | 69.711 ms |

Relative readout:

- **11.98× faster than Python**

The current v4.142.0 async harness emitted Python comparison cells but
not a populated live Go table; this is called out explicitly in
`benchmarks/FINAL_REPORT_v4.143.md`.

---

## 4. Fixed-point status

**NEAR FIXED POINT.**

| Artifact | Lines | md5 |
|---|---:|---|
| `/tmp/stage2.ll` | **109,872** | `6d4963cdbe060ac1cee85eb58f2fa932` |
| `/tmp/stage3.ll` | **109,872** | `dddf64c3a77ed9236c82de517bc055d1` |

`verify_fixed_point.sh --keep` reports **4 diff lines out of 109,872**,
all the known version-placeholder metadata boundary.

Source: `docs/roadmap/v4/v4.142.0/FIXEDPOINT_STATUS.md`

---

## 5. Sanitizers

| Class | v4.135.0 | **v4.142.0** |
|---|---:|---:|
| Valgrind CLEAN | 0 | **0** |
| Valgrind WARNINGS_ONLY | 60 | **66** |
| Valgrind ERRORS | 5 | **0** |
| ASan CLEAN | 54 | **55** |
| ASan ASAN_ERROR | 0 | **0** |
| ASan CRASH_NO_ASAN | 11 | **11** |

**Headline:** Ge.1 is closed. The five residual generic-monomorphization
valgrind ERRORS from v4.135.0 are gone.

The additional clean ASan cell is the new `66_qualified_type_ref.mn`
golden. The 11 residual ASan non-clean outcomes are still the
async/tensor/closure-typed feature-gap cohort, not memory-safety bugs.

Sources:

- `docs/roadmap/v4/v4.142.0/VALGRIND_REPORT.md`
- `docs/roadmap/v4/v4.142.0/ASAN_REPORT.md`

---

## 6. Flaky audit

No new 5x flaky audit was run at v4.142.0. The active cumulative audit
base remains the v4.141.0 result:

- **25 sequential non-bootstrap pytest runs**
- **0 flaky findings**

Reference:

- `docs/roadmap/v4/v4.141.0/FLAKY_AUDIT.md`

---

## 7. Dead code / structural cleanup

No new dead-code sweep shipped in this release. The v4.123.0 removal of
`optimizer.py` and the subsequent closeout-arc cleanup claims remain the
standing baseline.

---

## 8. Carry-forward and docket state

Closed in the v4.137.0–v4.142.0 bridge line:

- Ch.1
- Bo.1 / Bo.2 / Bo.3 / Bo.4 / Bo.5 / Bo.6 / Bo.7
- Gr.2
- Sem.1
- §0 / Co.1 documentation precision carry-forward
- Dr.1
- Cb.5
- SE.1
- Cb.3
- An.2
- **Ge.1**

Net ledger state at v4.142.0:

- **63 opened**
- **48 closed**
- **15 open**
- **0 CRITICAL · 0 HIGH · 8 MEDIUM · 7 LOW**

Remaining open work is now feature-gap / ecosystem / test-hygiene scope:

- Sh.4 / Sh.5 / Sh.6 / Sh.7 / Sh.9a / Sh.9b / Sh.10
- ABI.1
- Rt.2 / Rt.3
- Gr.1
- TR.1 / Bn.1 / Tm.1

---

## 9. Panel score history

| Release | Aggregate | Outcome |
|---|---:|---|
| v4.120.0 | 8.21 | Option B |
| v4.136.0 | **8.80** | **Option C (`v5.0.0-rc1`)** |
| **v4.143.0 forecast** | **~9.18** | projection only |

The forecast is not a claim of decision, only a working projection from
the closure of the full v4.136.0 carry-forward stack plus Ge.1.

---

## Evidence index

- `docs/roadmap/v4/v4.142.0/SESSION_REPORT.md`
- `docs/roadmap/v4/v4.142.0/FIXEDPOINT_STATUS.md`
- `docs/roadmap/v4/v4.142.0/VALGRIND_REPORT.md`
- `docs/roadmap/v4/v4.142.0/ASAN_REPORT.md`
- `docs/roadmap/v4/v4.142.0/V5_READINESS.md`
- `.reviews/v4.143.0/PRE_PANEL_AUDIT.md`
- `benchmarks/FINAL_REPORT_v4.143.md`
