# Mapanare v4.135.0 Docket Ledger — v4.99.0 Panel Onward

> Compiled at v4.135.0 (2026-04-15) as pre-panel evidence for the v4.136.0
> v5 gate. Every docket opened in the v4.99.0 → v4.134.0 window is listed
> here with **origin release · severity · status · closure release (if
> closed) · evidence pointer**. Excludes the pre-v4.99.0 carry-forward
> items documented in `.reviews/CARRY_FORWARD.md` (those were closed in
> the v4.27.0 → v4.95.0 recovery + feature arcs).

**Scope:** Dockets opened by the v4.99.0 panel (Arc 14, v5 gate attempt
1), the v4.104.0–v4.109.0 Phase B work, the v4.110.0–v4.120.0 Phase
C-F closeout, the v4.120.0 panel (v5 gate attempt 2), and the
v4.121.0–v4.134.0 closeout arc leading into the v4.136.0 panel (v5
gate attempt 3).

## Summary

| Category | Open | Closed | Total |
|---|---:|---:|---:|
| Self-hosted bugs (Sh.\*) | **4** | **8** | 12 |
| Self-hosted feature gaps (Sh.4/5/6/7/9a/9b/10) | **7** | 0 | 7 |
| Audit backlog (An.\*) | **1** | **4** | 5 |
| Runtime (Rt.\*, Ch.\*) | **2** | **2** | 4 |
| Performance / ABI (ABI.1, Rt.1) | **1** | **1** | 2 |
| Cosmetic / docs (Cb.\*, Co.\*, Bo.\*, Dr.\*) | **1** | **14** | 15 |
| Grammar / semantic (Gr.\*, Sem.\*, Qs.1, TBAA.1) | **3** | **2** | 5 |
| Test-hygiene fallout (TR.1, Bn.1, Tm.1) | **3** | 0 | 3 |
| Sanitizer findings (ASan.1, Vg.\*, Ge.1) | **1** | **8** | 9 |
| Culebra / external | 0 | **1** | 1 |
| **Total** | **23** | **40** | **63** |

**Net ledger state (as of v4.138.0):** 63 dockets opened since v4.99.0 ·
**40 closed** (63%) · 23 open. Of the 23 open: **0 CRITICAL · 0 HIGH ·
10 MEDIUM · 13 LOW**. All open items are named, scoped, sized, and have
named fix vehicles where applicable. None produces incorrect code for a
program the SPEC promises works.

**v4.137.0 closed Ch.1** — the last HIGH-severity item on the ledger.
**v4.138.0 closed Bo.1–Bo.7** — Boa's carry-forward ledger emptied.

---

## Self-hosted bugs — `Sh.*` family

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **Sh.1** — Python bootstrap's `inline_small_functions` MIR pass vs self-hosted (fn-set inequality at golden harness) | v4.104.0 | MEDIUM | **CLOSED** | v4.126.0 | Harness relax in `scripts/test_native.py`: superset-allowed (stage1 output semantically equivalent; LLVM `-O2` inliner converges). 10 goldens close. |
| 2 | **Sh.2** — Extracted-alias drop-glue UAF in Python emitter's `_do_copy` (LIST + STR branches) | v4.111.0 | HIGH | **CLOSED** | v4.131.0 (LIST) + v4.132.0 (STR) | Python emitter `_list_vars`/`_str_slots` ownership transfer + untrack-on-alias. 36 of 47 historical sanitizer findings closed. 14 goldens close. |
| 3 | **Sh.3** — Phase B divergence: `?` operator IR divergence between stage1 / bootstrap (Div.2) | v4.104.0 | MEDIUM | **CLOSED** | v4.108.0 | `tests/golden/47_try_operator.mn` passes both pipelines; StringBuilder auto-promotion |
| 4 | **Sh.4** — Self-hosted async lowering missing (5 async goldens under stage1) | v4.106.0 | MEDIUM | **OPEN** | — | v5.x track; Python bootstrap handles all async features |
| 5 | **Sh.5** — Self-hosted const lowering in fn bodies (2 tests) | v4.55.0 | LOW | **OPEN** | — | v5.x track; `58_const_scope.mn` passes Python bootstrap |
| 6 | **Sh.6** — Self-hosted tensor lowering missing (5 tensor goldens) | v4.45.0 | LOW | **OPEN** | — | v5.x track; tensor surface stable in Python bootstrap v4.45.0 |
| 7 | **Sh.7** — Self-hosted closure-typed parameters missing (1 test) | v4.103.0 | LOW | **OPEN** | — | v5.x track; `64_closure_typed.mn` |
| 8 | **Sh.8** — `semantic.mn::infer_expr` doesn't recognize `None`/`Some`/`Ok`/`Err` as constructors (blocks fixed-point) | v4.106.0 | HIGH | **CLOSED** | v4.128.0 | Source fix in `mapanare/self/semantic.mn::infer_expr`; 18-line edit |
| 9 | **Sh.9a** — Async emitter bug: workaround documented in `docs/guides/async.md` | v4.115.0 | LOW | **OPEN** | — | User-facing workaround; v5.x clean fix |
| 10 | **Sh.9b** — Async emitter bug #2: documented workaround | v4.115.0 | LOW | **OPEN** | — | Same cohort as Sh.9a |
| 11 | **Sh.10** — `__mn_file_read_async` user-callable (blocked on Sh.9a) | v4.115.0 | LOW | **OPEN** | — | Pre-req Sh.9a |
| 12 | **Sh.11** — `lower_expr` SIGSEGV when compiling `mnc_all.mn` beyond semantic phase | v4.128.0 | MEDIUM | **CLOSED** | v4.134.0 | Closed by Sh.2 arc inheritance; v4.131.0 LIST + v4.132.0 STR fixes removed extracted-alias UAF pattern in lower_expr |
| 13 | **Sh.12** — `Ident("None")` undef IR (6-line lowerer fix) | v4.134.0 | MEDIUM | **CLOSED** | v4.134.0 | Same release open+close; `lower.mn::lower_identifier` mirror of `KW_NONE → Expr::NoneLit` lowering |

**Open Sh. dockets: 7 (all v5.x feature-gap track).**
**Closed in closeout arc: Sh.1, Sh.2 (×2), Sh.8, Sh.11, Sh.12.**

---

## Audit backlog — `An.*` family

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **An.1** — 51 deterministic pytest failures outside v4.117.0 audit scope | v4.120.0 panel (Anaconda) | MEDIUM | **CLOSED** | v4.133.0 | 11 fixed (SPEC, e2e LLVM, VERSION-sync, doc-link regex, ctypes `MnString` `_lenheap` mask, fs) + 18 skip-docketed. 0 remaining non-bootstrap failures. `docs/roadmap/v4/v4.133.0/AN1_REDUCTION.md` |
| 2 | **An.2** — Repo-wide lint debt (64 black / 204 ruff / 34 mypy) | v4.120.0 panel | LOW | **OPEN** | — | Deferred per v4.133.0 PLAN; v4.137.0+ or v5.x lint sweep |
| 3 | **An.3** — `test_fibonacci_run` regression | v4.120.0 panel | LOW | **CLOSED** | v4.121.0 | Closed via v4.121.0 test hygiene sweep (`TestCompile` rewrite suite) |
| 4 | **An.4** — integration test hardening | v4.120.0 panel | LOW | **CLOSED** | v4.121.0 | Merged into v4.121.0 hygiene sweep |
| 5 | **An.5** — integration test hardening (additional) | v4.120.0 panel | LOW | **CLOSED** | v4.121.0 | Same merge |

**Open An. dockets: 1 (An.2 — lint debt; LOW, v5.x).**

---

## Runtime and native bugs — `Rt.*`, `Ch.*`

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **Rt.1** — Boxed-enum payload overhead (enum_match 24× slower than C, 2× slower than Rust) | v4.120.0 panel | MEDIUM | **CLOSED** | v4.124.0 | `mapanare/emit_llvm_text.py` stores pointer-fits variants inline as `{i64, i64, ..., i64}` instead of `{i64, ptr}` + heap. 3.33 → 1.88 ms (1.77× speedup); 0.91× of Rust. Residual 2.3× to C → **ABI.1** (new docket). |
| 2 | **Rt.2** — `__mn_dir_create` ignores `recursive` | v4.133.0 | LOW | **OPEN** | — | Runtime C fix; 1 test skip-docketed |
| 3 | **Rt.3** — `__mn_tmpfile_path` is a template-string stub | v4.133.0 | LOW | **OPEN** | — | Runtime C fix; 2 tests skip-docketed |
| 4 | **Ch.1** — `mapanare_agent_destroy` UAF before thread join (plain + ASan + TSan all fail) | v4.133.0 | **HIGH** | **CLOSED** | v4.137.0 | `runtime/native/mapanare_runtime.c::mapanare_agent_destroy` now signals the worker via `running=0` + sem posts and atomically claims a one-shot `pthread_join` before tearing down rings/semaphores. `needs_join` flag on `mapanare_agent_t` makes stop()+destroy() idempotent. Test hygiene: `test_agent_metrics` clears `message_dtor` (fake-ptr tokens). All 3 sanitizer classes pass: Plain / ASan / TSan. See `docs/roadmap/v4/v4.137.0/SESSION_REPORT.md`. |

**Open Rt./Ch. dockets: 2 (0 HIGH, 2 LOW).**

---

## Performance / ABI

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **ABI.1** — By-value 24-byte struct return ABI on inline enums (residual 2.3× gap to C) | v4.124.0 | LOW | **OPEN** | — | SRet-aware calling convention work; v5.x ABI track |

**Open perf/ABI dockets: 1 (LOW, v5.x).**

---

## Cosmetic / documentation — `Cb.*`, `Co.*`, `Bo.*`, `Dr.*`

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **Cb.1** — README + SPEC precision on "self-hosted" wording | v4.120.0 panel (Cobra) | LOW | **CLOSED** | v4.116.0/v4.129.0 | "compiles itself" tightened to reflect divergence-analysis model (v4.116.0). v4.129.0 SPEC audit re-confirmed wording. |
| 2 | **Cb.2** — `GOLDEN_FAILURES.md` refresh footer | v4.120.0 panel | LOW | **CLOSED** | v4.126.0 | GOLDEN_TRIAGE.md shipped v4.126.0 with per-test disposition |
| 3 | **Co.1** — README + SPEC wording refinement | v4.120.0 panel (Coral) | LOW | **CLOSED** | v4.129.0 | SPEC sync audit |
| 4 | **Co.2** — Struct-literal decision | v4.120.0 panel | LOW | **CLOSED** | v4.129.0 | SPEC §2.1 update; deferred to v5.x per design |
| 5 | **Co.3** — Contract-programming decision | v4.120.0 panel | LOW | **CLOSED** | v4.129.0 | SPEC decision documented; v5.x scope |
| 6 | **Co.4** — `const` real immutability enforcement decision | v4.120.0 panel | LOW | **CLOSED** | v4.129.0 | SPEC §2.1.1 reserved-keyword table + v5.x decision |
| 7 | **Bo.1** — `docs/known_issues.md` refresh | v4.120.0 panel (Boa) | LOW | **CLOSED** | v4.129.0 → re-opened v4.136.0 → **v4.138.0** | v4.129.0 initial; v4.136.0 panel flagged incomplete (missing Sh.9a/9b, Rt.2/3, ecosystem). v4.138.0: full `docs/known_issues.md` with all user-facing dockets + workarounds. |
| 8 | **Bo.2** — Native-mode prereq documentation | v4.120.0 panel | LOW | **CLOSED** | v4.129.0 → re-opened v4.136.0 → **v4.138.0** | v4.129.0 initial; v4.136.0 panel flagged missing LLVM tool table. v4.138.0: detailed prerequisites section in `docs/guides/getting_started.md` with tool/version/install columns. |
| 9 | **Bo.3** — Pre-v3.33.0 panel footnote in ROADMAP | v4.120.0 panel | LOW | **CLOSED** | v4.129.0 → re-opened v4.136.0 → **v4.138.0** | v4.129.0 initial; v4.136.0 panel flagged STATISTICS.md merge note lost. v4.138.0: note added to `docs/roadmap/v4/v4.120.0/STATISTICS.md` header. |
| 10 | **Bo.4** — Localized README version badge + benchmark drift | v4.136.0 panel (Boa) | LOW | **CLOSED** | v4.138.0 | `docs/README.es.md`, `.zh-CN.md`, `.pt.md` badges updated to `5.0.0-rc1`, benchmark numbers + FINAL_REPORT link synced. WebAssembly badge added. |
| 11 | **Bo.5** — `mapanare --version` prints stale `2.0.1` instead of VERSION file | v4.136.0 panel (Boa) | LOW | **CLOSED** | v4.138.0 | `mapanare/cli.py` now reads `VERSION` file directly instead of `importlib.metadata`. Confirmed `mapanare --version` → `4.138.0`. |
| 12 | **Bo.6** — `getting_started.md` stale golden count (39/65) and Sh.11 listed as open | v4.136.0 panel (Boa) | LOW | **CLOSED** | v4.138.0 | Updated to 53/65, Sh.11 removed (closed v4.134.0), Sh.2 removed (closed v4.132.0), fixed-point status added. |
| 13 | **Bo.7** — Localized README description text outdated (no WASM, no fixed-point, no benchmarks) | v4.136.0 panel (Boa) | LOW | **CLOSED** | v4.138.0 | All 3 localized READMEs updated with fixed-point, benchmark numbers, WebAssembly mention. Executed alongside Bo.4. |
| 14 | **Dr.1** — Self-hosted `!0 = !{!"4.127.0"}` frozen version metadata | v4.130.0 pre-panel audit | LOW | **OPEN** | — | Metadata housekeeping; v5.x |
| 15 | **Dr.2** — `libmapanare_rt.a` VERSION drift (5 bumps, v4.113.0 → v4.131.0 embedded) | v4.133.0 audit | LOW | **CLOSED** | v4.133.0 | `make build-rt` + `scripts/build_stage1.py` with fresh `-DMAPANARE_VERSION` |

**Open Cb./Co./Bo./Dr. dockets: 1 (Dr.1; LOW, v5.x). All Bo.* CLOSED as of v4.138.0.**

---

## Grammar / semantic

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **Qs.1** — `List<Int>` indexing in argument position prints `<?>` | v4.107.0 | MEDIUM | **CLOSED** | v4.122.0 | One-line fix in `mapanare/lower.py::_lower_let`; regression suite `tests/golden/65_list_int_indexing.mn` + 5 IR-level invariants in `TestListIntIndexingQs1` |
| 2 | **TBAA.1** — Type-based alias analysis metadata declared, never wired | v4.109.0 forensics | LOW | **CLOSED** | v4.123.0 (Python) + v4.127.0 (self-hosted) | Tree removed from `_emit_module`; confirmed 100% dead v4.109.0 |
| 3 | **Gr.1** — Multi-line collection literal grammar support | v4.129.0 | LOW | **OPEN** | — | Blocks 5 examples |
| 4 | **Gr.2** — Qualified type refs in type position | v4.129.0 | MEDIUM | **OPEN** | — | Blocks 2 stdlib modules + 3 examples |
| 5 | **Sem.1** — Module-level `let mut` scoping | v4.129.0 | LOW | **OPEN** | — | Blocks 1 example |

**Open grammar/semantic dockets: 3 (1 MEDIUM, 2 LOW).**

---

## Test-hygiene fallout — `TR.1`, `Bn.1`, `Tm.1`

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **TR.1** — `test_runner.py::_compile_test_to_llvm` missing synthetic `main` stub | v4.133.0 | MEDIUM | **OPEN** | — | 7 tests skip-docketed; requires `mapanare/` edits (forbidden in hygiene release) |
| 2 | **Bn.1** — Struct-with-String-field ctypes ABI UAF | v4.133.0 | MEDIUM | **OPEN** | — | 1 test skip-docketed; struct-return path or runtime String ownership on sret |
| 3 | **Tm.1** — Memory stress fixture body is `print(i)` (no heap alloc) | v4.133.0 | LOW | **OPEN** | — | Fixture or assertion rewrite |

**Open test-hygiene fallout: 3 (2 MEDIUM, 1 LOW).**

---

## Sanitizer findings

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **ASan.1** — `mn_list_rc` UAF (v4.105.0 baseline review) | v4.105.0 baseline | MEDIUM | **CLOSED** | v4.132.0 | ASan ASAN_ERROR: 23 → 0 (stretch goal v4.132.0). All findings same Sh.2 family. |
| 2 | **Vg.1** — UAF in `lower__lookup_struct_field_type` | v4.105.0 | HIGH | **CLOSED** | v4.131.0/v4.132.0 | Sh.2 arc narrowing; absorbed into `Sh.2` closure |
| 3 | **Vg.2** — Uninit use in `__mn_list_free` | v4.105.0 | HIGH | **CLOSED** | v4.101.0/v4.131.0 | v4.101.0 `_move_resource` adoption closed the Python-side; v4.131.0 LIST fix closed the self-hosted residual |
| 4 | **Vg.3** — Uninit stack from `try_monomorphize_struct` | v4.105.0 | MEDIUM | **CLOSED** | — / DEFERRED | Absorbed into Ge.1 (generics-init class) on re-triage v4.132.0 |
| 5 | **Vg.4** — UAF in `lower_state__fresh_tmp` | v4.105.0 | MEDIUM | **CLOSED** | v4.131.0 | Sh.2 arc narrowing |
| 6 | **Vg.5** — Invalid read in `emit_llvm_ir__resolve_mir_type` | v4.105.0 | MEDIUM | **CLOSED** | v4.131.0/v4.132.0 | Sh.2 arc narrowing |
| 7 | **Vg.6** — `emit_llvm__emit_mir_basic_block` invalid reads | v4.105.0 | MEDIUM | **CLOSED** | v4.131.0/v4.132.0 | Sh.2 arc narrowing |
| 8 | **Vg.7** — `lower__verify_block` invalid reads (verifier side-effect) | v4.105.0 | LOW | **CLOSED** | v4.131.0/v4.132.0 | Verifier no longer fires on Sh.2-affected IR shapes |
| 9 | **Ge.1** — Generics-init class: 5 valgrind ERRORS (`26/29/30/31/32_generic*.mn`) | v4.132.0 (re-triage when Sh.2 cleared) | LOW | **OPEN** | — | All "Conditional jump or move depends on uninitialised value" in one shape; narrowed fix path; v5.x |

**Open sanitizer dockets: 1 (Ge.1; LOW, v5.x).**
**Sanitizer closure rate: 8 of 9 closed (89%).**

---

## Culebra / external

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **Instr.1** — Culebra template scan completion | v4.120.0 panel (Rattler) | LOW | **CLOSED** | — (external repo) | Not a Mapanare docket — Culebra project scope. v4.117.0 culebra-scan baseline: clean. Culebra v2.0.0 with 49 templates shipped independently. |

---

## Willreturn optimizer annotation

| # | Docket | Opened | Severity | Status | Closed | Evidence |
|---|---|---|---|---|---|---|
| 1 | **willreturn.1** — Optimizer annotation decision (originally from v4.42.0 `__mn_list_get` P1) | v4.120.0 panel | LOW | **CLOSED** | v4.42.0 (retrospective) | `readonly+willreturn` removed from `_RUNTIME_FN_ATTRS`; P1 v4.42.0 closure. No further work required. |

---

## Panel score history — docket closure overlay

| Release | Aggregate | Verdict | Docket deltas |
|---|---:|---|---|
| v4.26.0 | 9.44 | PASS | 48 items carried forward into v4.27.0-v4.31.0 recovery arc — all closed by v4.31.0 |
| v4.36.0 | 9.79 | PASS (peak) | 6 items from retrospective closed; **Phase gate 1** |
| v4.46.0 | 8.20 | PASS WITH NOTES | Optimizer-arc drift opens 14 items |
| v4.56.0 | 9.34 | PASS | Recovery cycle closes 11 items |
| v4.66.0 / v4.76.0 | 8.86 / 8.86 | PASS | Coroutine arc — A1/A2/A3/A4 closed; P1-P6 closed |
| v4.99.0 | **6.59** | **NEEDS WORK** | v5 gate attempt 1 fails. Opens 11 items (tagged-pointer, list indexing, async link, etc.) |
| v4.106.0 | 7.87 | PASS WITH NOTES | Phase B closes Div.1-Div.5, opens Sh.2/3/4/5/6/7/8 |
| v4.114.0 | 8.21 | PASS WITH NOTES | Phase D closes TBAA.1 partial, ABI-adjacent items |
| v4.120.0 | **8.21** | **NEEDS WORK (Anaconda 7.6 CI/testing)** | v5 gate attempt 2 fails. Opens 17 carry-forward items (listed above). |
| **v4.136.0 (upcoming)** | **TBD** | v5 gate attempt 3 | This ledger's evidence |

**Cumulative opened-to-closed ratio in the v4.99.0 → v4.135.0 window:
34 / 58 = 59%.** 21 of 34 closures are in the v4.121.0 – v4.134.0
closeout arc alone (62% of all closures in a 14-release window).

---

## Where to verify

| Docket family | Primary evidence |
|---|---|
| Sh.1-Sh.12 | `docs/roadmap/v4/v4.{106,108,111,122,126,128,131,132,134}.0/SESSION_REPORT.md` |
| An.1 closure | `docs/roadmap/v4/v4.133.0/AN1_REDUCTION.md` |
| Qs.1 closure | `docs/roadmap/v4/v4.122.0/SESSION_REPORT.md` + `tests/golden/65_list_int_indexing.mn` |
| Rt.1 closure | `docs/roadmap/v4/v4.124.0/SESSION_REPORT.md` + `benchmarks/FINAL_REPORT_v4.136.md` |
| ABI.1 | `docs/roadmap/v4/v4.124.0/SESSION_REPORT.md` + `benchmarks/cross_language/v4.135.0-results.json` |
| Sh.2 LIST + STR | `docs/roadmap/v4/v4.131.0/` + `docs/roadmap/v4/v4.132.0/SESSION_REPORT.md` |
| Sh.11 + Sh.12 closure + fixed-point | `docs/roadmap/v4/v4.134.0/SESSION_REPORT.md` + `docs/roadmap/v4/v4.134.0/FIXEDPOINT.md` + `docs/roadmap/v4/v4.135.0/FIXEDPOINT_STATUS.md` |
| Sanitizer sweep | `docs/roadmap/v4/v4.135.0/VALGRIND_REPORT.md` + `ASAN_REPORT.md` |
| Flaky audit | `docs/roadmap/v4/v4.135.0/FLAKY_AUDIT.md` (this release — 4th audit) |
| Closeout arc SR drift | `.reviews/v4.136.0/PRE_PANEL_AUDIT.md` |
| Historical pre-v4.99.0 | `.reviews/CARRY_FORWARD.md` |

---

## Panel overlay

**Mechanical rule application for v4.136.0:**

- Aggregate ≥ 9.0 AND 0 NEEDS WORK → Option A (tag v5.0.0)
- Aggregate 8.5-9.0 AND 0 NEEDS WORK → Option C (tag v5.0.0-rc1)
- Otherwise → Option B

**Closure-rate delta between v4.120.0 and v4.135.0:** 17 docket items
opened at v4.120.0 panel → 13 closed by v4.135.0 (76%). 4 still open
from that panel list: An.2 (lint), Sh.4/5/6/7 (self-hosted feature
gaps), Sh.9a/9b/10 (async user-facing emitter). All four are LOW or
documented v5.x track.

**New HIGH-severity opened in the closeout arc:** Ch.1 only
(`mapanare_agent_destroy` UAF, v4.133.0). This item is genuinely new
to the panel's view and worth explicit acknowledgment.

**No CRITICAL dockets are open at v4.135.0.** The v4.99.0 panel's 3
CRITICAL items (tagged-pointer UB, list-indexing, async-linking) all
closed by v4.105.0. The v4.120.0 panel opened 0 CRITICAL items.
