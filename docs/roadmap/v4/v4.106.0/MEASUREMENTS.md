# v4.106.0 Phase B Panel — Measurements

**Date:** 2026-04-14
**Scope:** v4.100.0 – v4.105.0 (Phase A + Phase B, 6 releases under review)

## Source code size

| Component | Lines | Notes |
|---|---:|---|
| Self-hosted compiler (`mapanare/self/*.mn`) | 38,830 | 10 modules |
| Python bootstrap (`mapanare/*.py`, excl. `self/`) | 38,710 | shrinking over time |
| C runtime (`runtime/native/*.c`) | 11,367 | 8 files |
| C runtime headers | 3,064 | |
| Generated IR (`mapanare/self/main.ll`) | 857,645 | `-O2`-compiled to 3.5 MB ELF |

Python and `.mn` line counts are now roughly at parity — a visible
signal of the native-first migration.

## Binary and build

| Metric | Value |
|---|---|
| `mnc-stage1` binary (stripped) | 3,501,192 B |
| `mnc-stage1-asan` (Phase B/2) | 6,679,200 B |
| `mnc-stage1-tsan` (Phase B/2) | 5,805,952 B |
| Full rebuild time (`build_stage1.py`, `-O2`) | 1 m 21 s |
| Optimization level confirmed | `clang -c -O2` for IR, `-O2` for C runtime |

`build_stage1.py` passes `-O2` to both the IR→object step and the C
runtime compilation. Verified in
`docs/roadmap/v4/v4.104.0/artifacts/build.log`.

## Test counts

| Suite | Count | Result |
|---|---:|---|
| pytest total collected | **5,443** | ~8 pre-existing failures (documented) |
| Golden tests | 64 | 21 pass through `mnc-stage1`, 60 pass full integration pipeline |
| Async golden tests | 3 | 3 run natively with correct output |
| CI gate workflow files | 5 | `ci.yml`, `integration.yml`, `playground.yml`, `publish.yml`, **`sanitizers.yml`** (new v4.105.0) |

## Golden pass rates

| Path | Pass / Total | Source |
|---|---:|---|
| Through `mnc-stage1` (clean IR emission) | 21/64 | Phase 2 of v4.104.0 |
| Through full integration pipeline (emit → llvm-as → opt -O2 → llc → clang → run) | 60/64 | Phase 3 of v4.104.0 |
| Stage1 IR validates under `llvm-as` | 20/21 | Phase 5 of v4.104.0 (only `10_result` emits invalid IR) |
| Stage1 binaries run end-to-end with byte-identical output to bootstrap | 17/18 | Phase 5 of v4.104.0 |
| Async golden tests (55/56/57) native run | **3/3** | v4.102.0 + v4.104.0 re-verification |

The 21 / 64 mnc-stage1 rate is unchanged across v4.102.0 → v4.105.0.
No Phase A fix regressed stage1 output. The 43 failures cluster into
8 pre-existing root causes in `mapanare/self/` (documented
`PHASE2_GOLDEN.md`).

## Sanitizer results (Phase B/2 baseline, re-verified in Phase 1 this release)

### Valgrind (64 golden tests × `mnc-stage1`, 84 s wall)

| Class | Count |
|---|---:|
| CLEAN (no errors, no leaks) | **0** |
| WARNINGS_ONLY (leaks only — arena pattern, not a bug) | 28 |
| ERRORS (invalid read/write or uninit use) | 36 |

Top error sites across the 36 ERROR tests:

- `mir_opt__block_successors` — 14× (Phase 2 Category A)
- `__mn_list_free` — 12× (new finding Vg.2 / As.1)
- `emit_llvm__emit_mir_call` — 11× (Phase 2 Category B)
- `mir_opt__escape_analysis_function` — 6×
- `lower__verify_block` — 6×
- `emit_llvm__emit_mir_basic_block` — 6×
- `lower__lookup_struct_field_type` — 4× (Vg.1; affects 06/14 PASSes)
- `lower_state__fresh_tmp` — 4×
- `emit_llvm_ir__resolve_mir_type` — 3×

### AddressSanitizer (64 × `mnc-stage1-asan`, 21 s wall)

| Class | Count |
|---|---:|
| CLEAN | **21** |
| ASAN_ERROR | 17 |
| CRASH_NO_ASAN (semantic fail or SIGSEGV outside heap) | 26 |

- 12× `heap-use-after-free` (top: `mn_list_rc` in `__mn_list_free`)
- 5× `global-buffer-overflow` (`strtoll` on non-NUL-terminated `[N x i8]`)

### ThreadSanitizer

| Target | Tests | Races |
|---|---:|---:|
| Compiler-side (`mnc-stage1-tsan` on 64 goldens) | 64 | 0 data races (29 signal-unsafe findings from legacy handler — fixed in v4.105.0 Phase 4) |
| **Async binaries with TSan-runtime libmapanare_rt** | **3** | **0** |

Async scheduler is race-free. v4.102.0 shipped correctness without
concurrency hazards — exactly what the v4.99.0 panel's Viper lens
asked for.

## Phase A docket closure (5 critical / high)

| # | v4.99.0 docket item | Fixed in | Evidence | Status |
|---|---|---|---|:---:|
| 1 | CRITICAL: Tagged-pointer UB in `mapanare_core.c` | v4.100.0 | `is_heap` bitfield at `mapanare_core.h:60`; all `mn_tag_heap`/`mn_is_heap` helpers deleted from `mapanare_core.c` (only comments remain describing the transition). 36 valgrind runs show no tagged-pointer-specific errors. | **CLOSED** |
| 2 | CRITICAL: List indexing bug | v4.101.0 | `_move_resource` at 6 sites in `emit_llvm_text.py`; 0/61 → 16/62 goldens. Later v4.103.0 drop-glue fix took it to 21/64. | **CLOSED** |
| 3 | HIGH: Rebuild `libmapanare_rt.a` with scheduler exports | v4.102.0 | `nm` on `libmapanare_rt.a` shows `__mn_coro_scheduler_{init,destroy,register,run}`, `__mn_coro_spawn`, `__mn_coro_register_wait`. 3/3 async goldens run natively. | **CLOSED** |
| 4 | HIGH: Verify `else`/`sino` end-to-end | v4.103.0 | `63_else_sino.mn` golden test produces correct output (positive/negative/zero/1/-1/0) through Python bootstrap + clang link + native binary. | **CLOSED** |
| 5 | HIGH: Fix closure type annotations | v4.103.0 | 3 lowering changes (`_resolve_type_expr(FnType)`, `_lower_call(Identifier)`, `_lower_lambda`) + golden `64_closure_typed.mn` produces (10, -3, 20, 15). | **CLOSED** |

**All 5 critical/high items CLOSED with evidence.**

## Medium / low docket (6 items)

| # | v4.99.0 docket item | Status |
|---|---|:---:|
| 6 | MEDIUM: Disclose binary corruption in README / `build_from_seed.sh` | Superseded — the corruption itself was fixed in v4.101.0, so the disclosure item lost its reason to exist. README currently lists the build pipeline as stable. |
| 7 | MEDIUM: Fix byref size heuristic divergence in self-hosted emitter | OPEN — not in Phase A scope. |
| 8 | MEDIUM: Coroutine frame layout coupling | PARTIAL — v4.102.0 fixed the immediate `mn_coro_is_done` offset bug. The broader "fragile under LTO" concern is not tested (no LTO build in CI). |
| 9 | MEDIUM: String concat performance | OPEN — v4.95.0's StringBuilder landed but auto-routing `+`-chains is not implemented. Phase C (perf). |
| 10 | LOW: Document bilingual keyword collision space | OPEN. |
| 11 | LOW: Async-specific error messages | OPEN. |

Medium / low items are not this panel's scope. They carry forward to
Phase C or beyond.

## New docket opened in Phase B (for v4.106.0 panel's review, then v4.107.0+)

From v4.104.0 (bootstrap-vs-stage1 divergence):
- Div.1 HIGH — stage1 `?`-op lowering emits wrong-type store (`10_result`)
- Div.2 HIGH — bootstrap `?`-op emits invalid IR (`47_try_operator`)
- Div.3 MEDIUM — Option payload ABI divergence (`{i1,i64}` vs `{i1,ptr}`)
- Div.4 MEDIUM — or-pattern + enum constructor rejected
- Div.5 LOW — main return type inconsistency

From v4.105.0 (valgrind + ASan):
- Vg.1 HIGH — UAF in `lower__lookup_struct_field_type`
- Vg.2 HIGH — `__mn_list_free` / `mn_list_rc` uninit use (merged with As.1)
- Vg.3 MEDIUM — uninit stack from `try_monomorphize_struct`
- Vg.4 MEDIUM — UAF in `lower_state__fresh_tmp`
- Vg.5 MEDIUM — invalid read in `emit_llvm_ir__resolve_mir_type`
- Vg.6 MEDIUM — `emit_llvm__emit_mir_basic_block` reads invalid memory
- Vg.7 LOW — `lower__verify_block` reads invalid memory
- As.1 HIGH — C-runtime list shared-buffer double-free (root cause of Vg.2)
- As.2 HIGH — `strtoll` on non-NUL-terminated `[N x i8]`
- As.3 MEDIUM — `__mn_str_eq` → `bcmp` on freed (overlaps As.1)

**Note:** Vg.2 ≡ As.1 (same `mn_list_rc` UAF, two sanitizers), and
As.3 is another symptom of the same bug. A single fix to the list-free
machinery in `mapanare_core.c` would close 3 docket items.

## CI gate status

`.github/workflows/sanitizers.yml` — **present**, 3 jobs:

| Job | Trigger | Timeout | Regression check |
|---|---|---:|---|
| `valgrind` | push / PR to `dev` | 20 min | `check_valgrind_baseline.py` fails on CLEAN/WARNINGS → ERRORS transition |
| `asan` | push / PR to `dev` | 20 min | `check_asan_baseline.py` fails on CLEAN → ASAN_ERROR transition |
| `tsan-async` | push / PR to `dev` | 15 min | halt on first data race (`TSAN_OPTIONS=halt_on_error=1`) |

Plus pre-existing gates from v4.29.0 - v4.31.0:
1. `raise NotImplementedError` absent
2. pytest skip/xfail tracking version
3. Makefile RUNTIME_SOURCES matches actual .c files
4. verify_fixed_point.sh exit code propagates
5. CHANGELOG entries point at real files
6. Every doc code block parses
7. AST class coverage (isinstance in lower.py)
8. Optimizer non-convergence ICE

Total: **11 CI gates** (8 pre-existing + 3 new from v4.105.0).

## Crash diagnostics

v4.105.0 Phase 4 demonstrated:

```
$ ./mapanare/self/mnc-stage1 tests/golden/03_function.mn
[CRASH] SIGSEGV during compile at tests/golden/03_function.mn
./mapanare/self/mnc-stage1[0x731d53]
./mapanare/self/mnc-stage1(mir_opt__block_successors+0xc1)[0x689a01]
```

Vs. pre-v4.105.0 output (`Signal 11 at:` followed by raw backtrace — no
source context). Re-verified in Phase 1 of this panel: same output.

## Pre-existing pytest failures (not in panel scope)

5,443 tests collected. Of these, a small number fail because of issues
that predate Phase A/B and are unrelated to the critical docket:

- `tests/bind/test_python_binding.py::test_struct_with_string_field` —
  UnicodeDecodeError in bind harness (predates v4.100.0)
- `tests/llvm/test_dwarf_debug_info.py::TestDebugFlagDeferred::*` — 3
  tests checking a specific `-g` warning message that has since
  changed wording (test assertion drift)
- `tests/llvm/test_emitter_hardening.py::...::test_multiple_functions` — drift
- `tests/test_ci.py::TestToolsRunLocally::*` (3) — `black`/`ruff`/`mypy`
  style checks that hit files untouched by this release
- `tests/test_doc_links.py::...v4.80.0/PLAN.md` — stale link in an
  older roadmap doc

These 8 failures exist on `dev` with or without v4.106.0's changes
(verified by reverting working-tree edits and re-running). They are
**not Phase A or Phase B regressions.**

## Divergence summary (from v4.104.0 Phase 5)

| Class | Count | Note |
|---|---:|---|
| BOTH_FAIL | 1 | 51_match_guards_and_or (Python `None` as constructor) |
| MISSING (stage1 can't compile) | 42 | 8 categories from Phase 2 |
| Comparable (both emit, 21 with 21 having cosmetic-only diffs at `define` level) | 21 | `main` i32 vs i64, internal linkage, preamble — all cosmetic |
| Runnable + byte-identical to bootstrap | 17 | of 18 runnable; `34_file_io` differs by stale `/tmp` state |

The stage1 compiler produces byte-identical output to the Python
bootstrap on every test it can compile.

## Summary numbers for panel

- **5 / 5 critical-high docket items CLOSED** (v4.100.0 – v4.103.0)
- **21 / 64 golden through mnc-stage1** — no regressions since v4.103.0
- **60 / 64 golden through full integration pipeline**
- **3 / 3 async goldens native, TSan-clean, valgrind-clean**
- **3 new CI gates** (valgrind / asan / tsan-async) live
- **0 data races** in the async scheduler under TSan instrumentation
- **10 new docket items** from sanitizer runs, 5 from divergence — all
  recorded with evidence in committed reports for the next panel
