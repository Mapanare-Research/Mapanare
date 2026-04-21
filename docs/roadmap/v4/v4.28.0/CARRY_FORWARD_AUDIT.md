# v4.28.0 Carry-Forward Audit

> Phase 4 of `PLAN.md`. Every item from the v3.47.0 review's action list
> and the v4.26.0 panel's HIGH / MEDIUM queue is classified against its
> current status as of v4.28.0. Items with status `DEFERRED-*` have a
> target release and a reason. Items with no target release must be
> promoted to `INTENTIONALLY-IGNORED` with an explicit explanation; no
> item may sit in limbo.

## Legend

| Status | Meaning |
|---|---|
| `FIXED-IN-v4.27.0` | Closed by the v4.27.0 recovery release (8 CRITICAL items) |
| `FIXED-IN-v4.28.0` | Closed by this release |
| `DEFERRED-TO-v4.29.0` | Scheduled for the next recovery release — see reason |
| `DEFERRED-TO-v4.30.0` | Scheduled for the codegen / emitter recovery release — see reason |
| `DEFERRED-TO-v4.31.0` | Scheduled for the process-hardening recovery release — see reason |
| `DEFERRED-TO-v5.x` | Long-term; closed after the recovery arc terminates |
| `INTENTIONALLY-IGNORED` | Not going to fix, with reason |
| `NEVER-REAL` | Turned out to be based on a false assumption (e.g. revert-that-wasn't) |

## v3.47.0 review — hard blockers and should-fix items

The v3.47.0 panel was **7/7 PASS** — the release gate for v4.0.0. Three
reviewers attached conditional hard-blocker lists before v4.0.0 could
ship. The v4.26.0 panel subsequently found that most of the
conditionally-blocking items in `mapanare_gpu_builtins.c` were flagged
"must fix before v4.0.0" but **never actually committed**. See
[FORENSICS.md](./FORENSICS.md) for the git archaeology.

### v3.47.0 MUST-FIX (conditional hard blockers)

| # | Item | Source | Status | Notes |
|---|------|--------|--------|-------|
| 1 | Matmul shape malloc NULL check (`gpu_builtins.c:161-185`) | Cobra | **FIXED-IN-v4.28.0** | Phase 2.1. Also added dimension validation (Phase 2.2). Forensics: the v4.0.0 CHANGELOG claim was false — never committed. Regression-gated by `tests/runtime/tsan/matmul_validation.c`. |
| 2 | Matmul dimension validation (`gpu_builtins.c:161-185`) | Viper, Cobra | **FIXED-IN-v4.28.0** | Phase 2.2. Validates `left.cols == right.rows` + flat-length consistency + overflow-safe `m*k` / `k*n` via `__int128`. |
| 3 | GLSL temp file race (`mapanare_gpu.c:822-823`) | Viper | **FIXED-IN-v4.28.0** | Phase 2.3. `mkstemps` on POSIX, `GetTempFileNameW` on Windows. |
| 4 | Windows GPU init race (`mapanare_gpu.c:1059-1062`) | Cobra | **FIXED-IN-v4.28.0** | Phase 2.4. Replaced `InterlockedCompareExchange` double-check with `InitOnceExecuteOnce`. Same fix applied to four other Windows double-check sites the grep surfaced: signal mutex, intern table, tag strings, small-int cache. |

### v3.47.0 SHOULD-FIX (recommended but not blocking)

| Item | Source | Status | Notes |
|------|--------|--------|-------|
| `mn_init_tag_strings` not thread-safe (`core.c:2670-2671`) — 5th cycle at v3.47.0 | Viper, Mamba | **FIXED-IN-v4.28.0** | Phase 1.4. By v4.26.0 this was on its 7th carry-forward cycle — the longest-running runtime debt in the project. Closed with `pthread_once` (POSIX) / `InitOnceExecuteOnce` (Windows). |
| `tensor_from_list` borrow fragility | Viper | **DEFERRED-TO-v4.30.0** | The "borrow" model for the temporary tensor wrapper is correct in isolation but fragile under edits. Phase 1 of v4.30.0 (codegen + emitter work) will revisit the ownership model when the tensor API is extended for real `@gpu` dispatch. |

## v4.26.0 panel — CRITICAL + HIGH queue

### CRITICAL (all closed in v4.27.0)

| # | Item | Source | Status |
|---|------|--------|--------|
| 1 | `bind.py` no `argtypes`/`restype` | Mamba, Viper, Boa | **FIXED-IN-v4.27.0** |
| 2 | FFI DCE drops non-`main`-reachable functions | Boa | **FIXED-IN-v4.27.0** |
| 3 | `cli.py:1366` `.replace("define internal ", "define ")` sledgehammer | Rattler | **FIXED-IN-v4.27.0** |
| 4 | `libmapanare_rt.a` not built `-fPIC` | Boa, Mamba | **FIXED-IN-v4.27.0** |
| 5 | `@gpu`/`@cuda`/`@vulkan` `NotImplementedError` at `lower.py:986` | Rattler, Viper | **FIXED-IN-v4.27.0** (Path B: decorator removed) |
| 6 | `MIRVerifier` dead code in both pipelines | Anaconda | **FIXED-IN-v4.27.0** |
| 7 | `const` parser alias without `ConstDef` | Cobra, Coral, Viper, Boa | **FIXED-IN-v4.27.0** (Path B: keyword reverted) |
| 8 | Two parallel diagnostic systems; point-only spans | Anaconda | **FIXED-IN-v4.27.0** |

### HIGH (v4.28.0 scope + defers)

| Item | Source | Status | Notes |
|------|--------|--------|-------|
| CHANGELOG advertises non-parseable `Tensor<Float, [DIM, DIM]>` | Cobra, Coral | **FIXED-IN-v4.27.0** | Scrubbed from CHANGELOG, ROADMAP, SPEC. |
| `verify_fixed_point.sh` cannot fail (`EXIT=0`, no `set -e`) | Rattler, Anaconda | **DEFERRED-TO-v4.29.0** | v4.29.0 adds teeth to fixed-point verification. |
| `stage3.ll` zero-byte file from 2026-03-21 | Cobra, Rattler | **DEFERRED-TO-v4.29.0** | Tied to the fixed-point verification work in v4.29.0. |
| `mapanare/self/main.mn:32` stale `mapanare 4.7.1` (19 versions) | Rattler, Anaconda | **FIXED-IN-v4.28.0** | Phase 3. `VERSION` file is now substituted at build time; `test_mnc_stage1_version_matches_version_file` runs the binary. |
| `await` identity pass-through | Viper, Rattler | **DEFERRED-TO-v4.30.0** | Real coroutine lowering is a multi-hour task. v4.30.0 decides: implement via LLVM `llvm.coro.*` intrinsics OR strike the keyword. |
| `_emit_agent_wrap` no-op stub | Rattler | **DEFERRED-TO-v4.30.0** | Agent dispatch wiring is part of the v4.30.0 codegen recovery. |
| Signal / agent / registry concurrency races | Viper, Mamba | **FIXED-IN-v4.28.0** | Phase 1.1 (signal), 1.2 (agent inbox MPSC lock), 1.3 (type registry rwlock). TSan-clean stress tests. |
| Matmul v4.0.0 hard-blockers byte-identical to v3.47.0 | Cobra, Viper | **FIXED-IN-v4.28.0** | Phase 2.1 + 2.2. Forensics found the v4.0.0 claim was never committed. |
| Windows GPU init race propagated to signal mutex | Cobra | **FIXED-IN-v4.28.0** | Phase 1.1 + 1.4 + 2.4. All Windows double-check sites use `InitOnceExecuteOnce` now. |
| `extern "Python" fn` silently xfailed (79 tests) since v4.2.0 | Boa | **DEFERRED-TO-v4.29.0** | Decision path: restore against LLVM emitter OR delete the feature + unskip. |
| `mapanare_db.c` / `mapanare_html.c` orphaned (1,942 lines) | Anaconda | **DEFERRED-TO-v4.29.0** | Add both to the runtime build, declare exports, integration tests. |
| CHANGELOG advertises non-existent `tests/parser/test_const.py` etc. | Boa, Coral, Anaconda | **FIXED-IN-v4.27.0** | CHANGELOG rewritten with strikethrough corrections. |
| `const_def` parser transformer collapses `TypeExpr` to `.name` | Anaconda | **FIXED-IN-v4.27.0** | Transformer deleted alongside grammar revert. |
| Optimizer non-convergence is `logging.warning`, not ICE | Anaconda | **DEFERRED-TO-v4.30.0** | v4.30.0 promotes non-convergence to an internal compiler error. |
| Self-hosted DCE bounded loops + never calls `clean_phis_in_block` | Rattler | **DEFERRED-TO-v4.30.0** | Part of the v4.30.0 self-hosted optimizer work. |
| DWARF debug info not implemented (38 tests marked skip) | Rattler | **DEFERRED-TO-v4.31.0** OR **DEFERRED-TO-v5.x** | v4.31.0 makes the decision: strike the roadmap claim or ship `llvm.dbg.*` metadata emission. |
| `--no-check` flag bypasses semantic analysis silently | Anaconda | **DEFERRED-TO-v4.29.0** | Add stderr warning; consider renaming to `--unsafe-no-check`. |
| Makefile `build-rt` missing runtime files (4th cycle) | Anaconda | **DEFERRED-TO-v4.29.0** | v4.29.0 enumerates the complete runtime file list and adds a CI drift check. |

### MEDIUM (deferred by default)

| Item | Status | Target |
|------|--------|--------|
| User-Agent string `Mapanare/3.42` — 5 versions stale at v4.26.0 | **DEFERRED-TO-v4.31.0** | Process-hardening release. |
| `__mn_list_oob_buf` 4KB dead workaround (`core.c:972`) | **DEFERRED-TO-v4.31.0** | Dead-code sweep. |
| SPEC line 121 `di` label still wrong (5th cycle) | **DEFERRED-TO-v4.31.0** | Part of the SPEC sync. |
| Bilingual keywords table still missing from SPEC (3rd cycle) | **DEFERRED-TO-v4.31.0** | Part of the SPEC sync. |
| Spanish README out of sync (5+ cycle carry) | **DEFERRED-TO-v4.31.0** | Part of the SPEC sync. |
| Empty `[Unreleased]` section in CHANGELOG | **FIXED-IN-v4.27.0** | Normalised. |
| Six 7-cycle emitter carry-forwards (i64*, void()*, missing nsw, list bitcast, `__mn_map_new` arity, noalias/willreturn) | **DEFERRED-TO-v4.30.0** | The v4.30.0 release is dedicated to draining the emitter carry-forward queue. |

## Systemic process items (v4.31.0)

The v4.26.0 panel's finding that carry-forward resolution fell from
~64% to ~10% in a single cycle is not closed by the v4.28.0 fixes — it
is closed by the v4.31.0 CI gates. This audit exists to prevent the
same drift from happening between v4.28.0 and v4.31.0.

| Gate | Target | Rationale |
|------|--------|-----------|
| CHANGELOG honesty script | **v4.31.0** | Every `## [VERSION]` entry must map to a real file or test. Catches the class of failure that let v4.0.0 claim matmul fixes that were never committed. |
| No-hardcoded-version grep | **v4.31.0** | Any `"mapanare X.Y.Z"` literal anywhere in the tree fails the build. v4.28.0 addresses the `main.mn` case via the `__MN_VERSION__` placeholder; the CI gate prevents future regressions. |
| No-hollow-feature script | **v4.31.0** | `raise NotImplementedError` in `lower.py` or `emit_*.py` fails the build. |
| Carry-forward queue file | **v4.31.0** | `.reviews/CARRY_FORWARD.md` — every open item has a target release. No item may be added to the queue without a reason. |
| TSan-on-demand target | **v4.31.0** (this release adds the stress tests; v4.31.0 wires them into CI) | `make test-tsan` runs the three stress tests from v4.28.0. v4.31.0 plumbs it into the CI workflow. |

## Score trajectory (for reference)

| Version | Aggregate | Verdict |
|---------|-----------|---------|
| v3.47.0 | 9.79 | 7/7 PASS (release gate) |
| v4.26.0 | ~8.2 | 4 NEEDS WORK + 3 PASS WITH NOTES |
| v4.27.0 | ~8.7 (lead estimate, not panel) | — |
| **v4.28.0** | **~9.0 (lead estimate, not panel)** | — |
| v4.31.0 | ≥ 9.0 required for arc to terminate | **next 7-reviewer panel** |

The v4.31.0 panel is the only arbiter of when the recovery arc ends.
All internal self-grades in this audit are progress markers, not
release signals.

## Next review

The next 7-reviewer panel runs against **v4.31.0**. Items marked
`DEFERRED-TO-v4.29.0`, `DEFERRED-TO-v4.30.0`, and `DEFERRED-TO-v4.31.0`
in this audit must all show as `FIXED-IN-*` by then. Any item that
reaches the v4.31.0 panel still deferred is treated as a v4.31.0
failure.
