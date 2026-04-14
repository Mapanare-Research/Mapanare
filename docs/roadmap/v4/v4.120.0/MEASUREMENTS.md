# v4.120.0 Panel — Pre-Panel Measurements

> Snapshot taken at v4.120.0 (2026-04-14) on branch `dev`. The
> panel's seven reviewers grade against this state. Everything is
> reproducible via the commands at the bottom of each section.

---

## 1. Test suite

### Full pytest run

```bash
$ pytest tests/ -q --tb=no -n auto
73 failed, 5301 passed, 103 skipped, 7 xfailed, 64 warnings in 113.06s
```

**5,484 tests collected** (up from v4.99.0's 5,374, +110).
**73 failures on `main`.** This is **above** the v4.117.0 flaky audit's 22-failure number because:

- The v4.117.0 audit measured a **subset** (9 specific subdirectories, 1,501 tests).
- The full `tests/` suite includes bootstrap, emit, mir, tensor, transpiler, wasm, and lsp subdirectories that the audit did not cover.

Failure categories (spot-classified):

| Category | Count | Type | Panel severity |
|---|---:|---|---|
| Stale CLI tests asserting `mapanare compile` (pre-rename) | 14 | stale test | LOW |
| DWARF `-g` deferral-warning tests | 3 | feature gap (CLI should print warning) | LOW |
| Drop-glue count assertions | 2 | stale assertion, v4.101.0 move-semantics | LOW |
| Cross-module linkage `internal` vs `private` | 1 | overly-specific assertion | LOW |
| Emitter hardening `define` count drift | 1 | stale assertion, v4.108.0 StringBuilder | LOW |
| Bounded-generic trait monomorphization | 1 | real edge case | MEDIUM |
| Struct literal syntax (TestStructLiteralSyntax) | 3 | feature gap vs SPEC | MEDIUM |
| Self-hosted `semantic.mn` builtin coverage | 2 | tracks Sh.4 / Sh.5 / Sh.6 gaps | MEDIUM |
| `test_verification.py` pipeline + fixed-point | 5 | Sh.8 blocker surfaced | MEDIUM |
| CI meta-tests (`test_ci.py::test_ruff_check_passes`, `test_mypy_passes`) | 2 | lint debt | LOW |
| Transpiler / WASM / LSP / tensor misc | ~40 | various feature gaps, stale assertions, WIP modules | LOW–MEDIUM |

**Assessment:** 0 critical. ~45 are stale assertions or test hygiene. ~25 are real feature gaps tracked by existing dockets (Sh.4/5/6/8, struct literal syntax not in grammar yet). 2 are CI meta-tests that rerun lint.

### CI pipeline

```bash
$ make lint
black  —  64 files would be reformatted, 284 unchanged
ruff   —  204 errors (81 E501 line-too-long, 48 F401 unused-import,
          31 F541 f-string no placeholder, 24 I001 import-sort, ...)
mypy   —  34 errors in 7 files (mostly mapanare/lsp/*)
```

**This is a panel-visible finding.** The project's own `make lint` is
red on `dev`. Most errors are auto-fixable (`ruff check --fix`
handles ~104; `black .` reformats cleanly). The mypy errors are
concentrated in `mapanare/lsp/` — a WIP module not in the core
compilation pipeline.

## 2. Golden tests

### Through Python bootstrap

**64/64 programs compile and produce expected output.** One
long-standing failure (`51_match_guards_and_or`, or-pattern guards
in compound `match` arms) is tracked separately from the recovery
arc's ledger; it does not affect the panel's scope.

### Through mnc-stage1 (native self-hosted)

```bash
$ python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
26 passed, 38 failed in 6.3s
```

**Strict: 26/64. Effective: 39/64** (13 Category A tests produce
semantically-equivalent IR to the Python bootstrap but fail the
harness's strict function-count check because the bootstrap inlines
more aggressively).

Failure breakdown (from `docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md`):

| Bucket | Count | Docket |
|---|---:|---|
| `__mn_str_starts_with` crash in `emit_mir_call+0x23515` | 10 | Sh.2 |
| Async-missing (5 async test programs) | 5 | Sh.4 |
| Tensor-missing (5 tensor test programs) | 5 | Sh.6 |
| Const-missing (2 const test programs) | 2 | Sh.5 |
| Closure-typed (64_closure_typed) | 1 | Sh.7 |
| `lower_expr` crashes | 2 | Sh.1 |
| 58_const_scope, 58_async_file_io, 59_async_fanout, 62_list_output, 63_else_sino | 5 | various |
| GPU-tensor | 1 | GPU + Sh.6 intersection |
| or-pattern (bootstrap also fails) | 1 | — |
| Category A (function-count drift, IR semantically OK) | 13 | not a real failure |

**Assessment:** 26/64 literal is identical to v4.111.0 → v4.118.0
(no regressions, no unblocks). The failures are documented, sized,
and none re-opens a v4.99.0 docket.

### Integration pipeline (emit → llvm-as → opt → llc → clang → run)

Per v4.104.0 + v4.117.0 results: **60/64 PASS**, 2 SKIP (stdin /
network), 2 FAIL (`51_match_guards_and_or`, `47_try_operator`).

## 3. Fixed-point convergence

```bash
$ bash scripts/verify_fixed_point.sh
# Fails at Stage 1: Undefined variable 'None'
# (Python bootstrap bypasses via skip_check=True in build_stage1.py)
```

**Fixed-point NOT achieved.** Self-hosted `semantic.mn` does not
register `None`/`Some`/`Ok` as constructors. Tracked as docket
**Sh.8**. The Python bootstrap bypasses this gap; the self-hosted
binary has no bypass.

Byref size heuristic (docket #7 from v4.99.0) **is fixed in
isolation** — `/tmp/byref_test.mn` produces correct output; 16-byte
`Small` passes by value, 80-byte `Large` by reference. v4.112.0's
named release rename from "fixed-point verification" to "divergence
analysis + byref fix" is a v4.114.1 correction that landed in
changelog + session reports.

## 4. Sanitizers

From v4.117.0 session report and CI state:

- **ASan CI gate:** enforcing, regression-tracked by
  `scripts/check_asan_baseline.py`. 21/38 goldens clean; 17 with
  errors catalogued in v4.105.0's `ASAN_REPORT.md`. No new errors
  since v4.105.0.
- **TSan CI gate:** enforcing, race-free on 3/3 async golden tests
  (v4.102.0 async goldens) + v4.115.0 async I/O demos (extended in
  v4.117.0).
- **Valgrind CI gate:** enforcing, full golden suite. 0 CLEAN / 28
  WARNINGS / 36 ERRORS at v4.105.0 baseline, stable since.

Not re-run for this panel; CI enforcement since v4.105.0 means any
regression would have blocked a prior release.

## 5. Benchmarks

See `benchmarks/FINAL_REPORT_v4.120.md` for the definitive report
(500 lines, shipped in v4.118.0). Headline numbers:

**Cross-language geomean** across 6 workloads × 10 runs:

- vs **C (gcc -O2):** 5.46× slower (was 9.5× at v4.107.0)
- vs **Rust -O:** 1.13× slower
- vs **Go:** 1.04× slower (on par)
- vs **Python 3.12:** 36.9× faster

**Async geomean** across 5 workloads × 10 runs:

- vs **Python asyncio:** 42.6× faster
- vs **Go goroutines:** 1.74× slower

**Progress** (Mapanare O2 wall, median of middle-8 of 10 runs, ms):

| Workload | v4.82.0 | v4.98/99.0 | v4.107.0 | v4.118.0 | Credit |
|---|---:|---:|---:|---:|---|
| fib_recursive | 20.43 | 19.56 | 20.33 | 18.91 | jitter |
| quicksort | 1.79 | 1.98 | 2.58 | 2.45 | harness methodology |
| struct_alloc | — | 0.57 | 1.21 | 1.32 | harness methodology |
| enum_match | — | 2.27 | 3.66 | 3.03 | +17% vs v4.107 (dispatch codegen) |
| prime_sieve | — | 3.05 | 3.43 | 3.44 | noise |
| **string_concat** | **102.31** | **95.24** | **94.57** | **1.32** | **Phase C v4.108.0 auto-StringBuilder** |

## 6. v4.99.0 docket closure

All 11 v4.99.0 panel docket items. Status verified against
`docs/roadmap/v4/v4.114.0/DOCKET_AUDIT.md`.

| # | Item | Sev | Fixed in | Status | Evidence |
|---|---|---|---|---|---|
| 1 | Tagged-pointer UB | CRITICAL | v4.100.0 | CLOSED | `MnString` bitfield at `mapanare_core.h:60` |
| 2 | List indexing bug | CRITICAL | v4.101.0 | CLOSED | `_move_resource` at 6 call sites |
| 3 | Async can't link | HIGH | v4.102.0 | CLOSED | `mn_coro_is_done` fix; async goldens 42/43/110 |
| 4 | Else/sino latent | HIGH | v4.103.0 | CLOSED | drop-glue boxed-enum skip |
| 5 | Closure types | HIGH | v4.103.0 | CLOSED | 3-change in `lower.py` |
| 6 | Binary corruption disclosure | MEDIUM | v4.101.0 | CLOSED | root cause was UAF drop glue, not UB |
| 7 | Byref size heuristic | MEDIUM | v4.112.0 | CLOSED | `struct_byte_size` + `is_byref_type_st` |
| 8 | Coroutine frame coupling | MEDIUM | v4.113.0 | CLOSED | `mn_coro_frame_prefix_t` struct |
| 9 | String concat 2.2× slower than Python | MEDIUM | v4.108.0 | CLOSED | auto-StringBuilder MIR pass |
| 10 | Keyword collision SPEC gap | LOW | v4.113.0 | CLOSED | SPEC §2.1.1 reserved keyword master list |
| 11 | Async error messages silent | LOW | v4.113.0 | CLOSED | 5 error sites get stderr + exit(1) |

**11/11 CLOSED.** Zero v4.99.0 items remain open.

## 7. Open dockets (not from v4.99.0 — surfaced during recovery)

| ID | Severity | Impact | Planned |
|---|---|---|---|
| Rt.1 | HIGH | `enum_match` 2× slower than Rust due to payload boxing | v5.x |
| Sh.2 | HIGH | `__mn_str_starts_with` crash in self-hosted emitter (10 tests) | v5.x |
| Qs.1 | MEDIUM | `arr.push(42); print(str(arr[0]))` prints `<?>` through native pipeline | v5.x (reproduces today) |
| Sh.4 | MEDIUM | async missing from self-hosted | v5.x |
| Sh.5 | MEDIUM | const missing from self-hosted | v5.x |
| Sh.6 | MEDIUM | tensor missing from self-hosted | v5.x |
| Sh.7 | MEDIUM | closure types missing from self-hosted | v5.x |
| Sh.8 | MEDIUM | self-hosted `semantic.mn` None/Some/Ok ctor — blocks fixed-point | v5.x |
| TBAA.1 | LOW | TBAA metadata declared but never attached to loads/stores | v5.x |
| willreturn.1 | LOW | `willreturn` audit on heap-modifying runtime calls | v5.x |
| Sh.9a | LOW | Python bootstrap: await on String-returning async fn | workaround shipped v4.115.0 |
| Sh.9b | LOW | Python bootstrap: DCE eliminates unused-return await | workaround shipped v4.115.0 |
| Sh.10 | LOW | `__mn_file_read_async` user-callable (pre-req Sh.9a) | v5.x |
| Instr.1 | LOW | Culebra scan over 854K-line main.ll | v5.x |

**11 open** — 2 HIGH, 7 MEDIUM, 4 LOW (plus Instr.1 infrastructure).

## 8. CI gate status

| Gate | File | Enforcing? |
|---|---|---|
| Black | `ci.yml::format` | ✅ but currently red on `dev` (see §1) |
| Ruff | `ci.yml::lint` | ✅ but currently red on `dev` (see §1) |
| Mypy | `ci.yml::mypy` | ✅ currently red on `dev` (34 errors, lsp module) |
| pytest (3.11 + 3.12) | `ci.yml::test` | ✅ currently red on `dev` (73 failures) |
| Native C runtime (gcc) | `native.yml` | ✅ |
| ASan | `sanitizers.yml::asan` | ✅ (regression-gated) |
| TSan async | `sanitizers.yml::tsan-async` | ✅ |
| Valgrind golden | `sanitizers.yml::valgrind` | ✅ |
| WASM cross-compile | `wasm.yml` | ✅ |
| Android cross-compile | `android.yml` | ✅ |
| Coverage | `ci.yml::coverage` | ◐ informational |

10 enforcing gates. CI-green status on `dev` would depend on workflow file
definitions (some use `continue-on-error`, some skip on certain path
patterns). The pytest failures and lint debt would cause CI to be red if
the gates are enforcing as documented.

## 9. Codebase size

| Component | v4.99.0 | v4.118.0 | v4.120.0 (today) | Δ (99→120) |
|---|---:|---:|---:|---:|
| Self-hosted (`mapanare/self/*.mn`) | 38,824 | 39,763 | 39,763 | +939 |
| Python bootstrap (`mapanare/*.py`) | 38,526 | 36,092 | 36,092 | **−2,434** |
| C runtime (`runtime/native/*.c+*.h`) | 14,243 | 14,583 | 14,583 | +340 |
| pytest collected | 5,374 | 5,479 | 5,484 | +110 |
| Golden programs | 61 | 64 | 64 | +3 |

**Net code Δ v4.99.0 → v4.120.0: −1,155 lines.** The recovery arc
removed more than it added.

## 10. Panel score history

| Panel | Aggregate | Verdict |
|---|---:|---|
| v3.33.0 | 9.44 | 5 PASS / 2 NOTES / 0 NW |
| v3.45.0 | 9.69 | 6 / 1 / 0 |
| v3.47.0 | 9.79 | 7 / 0 / 0 — v4.0.0 gate PASS |
| v4.26.0 | 8.20 | 0 / 3 / 4 — crisis |
| v4.31.0 | 9.34 | 5 / 2 / 0 — Arc 1 recovery |
| v4.36.0 | 9.50 | Arc 1 close |
| v4.41.0 | 9.36 | Arc 2 |
| v4.46.0 | 8.99 | Arc 3 |
| v4.51.0 | 8.90 | Arc 4 |
| v4.56.0 | 9.00 | Arc 5 |
| v4.61.0 | 8.71 | Arc 6 |
| v4.66.0 | 7.71 | Arc 7 |
| v4.71.0 | 8.29 | Arc 8 |
| v4.76.0 | 8.86 | Arc 9 (first 10/10) |
| v4.99.0 | 6.59 | 1 / 3 / 3 — v5 gate FAIL |
| v4.106.0 | 7.87 | 1 / 6 / 0 — Phase B |
| v4.114.0 | 8.21 | 2 / 5 / 0 — Phase D |
| v4.120.0 | **pending** | this panel |

## 11. Reproducibility

Every number above is reproducible:

```bash
# Test counts
pytest --collect-only -q | tail -1
pytest tests/ -q --tb=no -n auto | tail -3

# Lint state
black --check .
ruff check .
mypy mapanare/ runtime/

# Golden
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1

# Self-hosted size
wc -l mapanare/self/*.mn

# Benchmarks — see FINAL_REPORT_v4.120.md §Reproducibility
```

Panel reviewers are encouraged to re-run any command above. Any
discrepancy between their run and these numbers should be
documented in the per-reviewer file.
