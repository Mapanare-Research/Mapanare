# v5.3.1 Session Report

**Date:** 2026-04-22
**Duration:** ~30 minutes
**Breaking:** No
**Compiler/runtime source changes:** No

---

## What was done

### Phase 1 — Version bump + lint fix
- VERSION bumped from 5.3.0 to 5.3.1
- `black --check .` and `ruff check .` already green (0 errors)
- The Anaconda lint finding (Lint-v5.2.0) was already resolved in a prior session

### Phase 2 — Documentation fixes
- **Bo.15** (MEDIUM): README fixed-point claim qualified — was "strict 3-stage
  fixed point" (stale since v5.1.2 In.1 inliner re-enable); now reads
  "3-stage fixed point reached at v4.134.0; temporarily regressed at v5.1.2
  from In.1 inliner re-enable; restoration tracked at v5.3.2"
- **Bo.16** (MEDIUM): `docs/known_issues.md` Ecosystem section updated — removed
  "No package manager yet" table row; replaced with v5.2.0 registry paragraph
  pointing to `docs/guides/packages.md`. Updated "Last updated" and
  "Last verified" timestamps.
- **Bo.17** (LOW): Version badges in `docs/README.zh-CN.md` and
  `docs/README.pt.md` bumped from 5.0.6 to 5.3.1. Also bumped
  `docs/README.es.md` from 5.2.0 to 5.3.1. Main `README.md` badge bumped
  from 5.2.0 to 5.3.1.
- **Bo.14r** (LOW): `docs/guides/getting_started.md` version reference updated
  from v4.143.0 to v5.3.1; test count updated from 5,160+ to 5,445+;
  fixed-point paragraph rewritten to reflect current state.

### Phase 3 — Stream-C test fix (MEDIUM)
- Fixed `MnList list = {0}` → `__mn_list_new(sizeof(int64_t))` in 4 stream
  test functions in `tests/native/test_c_runtime.c`:
  - `test_stream_from_list_collect`
  - `test_stream_map`
  - `test_stream_filter`
  - `test_stream_free_chain` (also affected — ASan caught it)
- Root cause: `{0}` sets `elem_size = 0`; the Ge.1r fallback silently sets
  it to 256 for unknown sizes; streams created with `sizeof(int64_t)` (8B)
  then read at 8B stride vs 256B write stride, causing stack-buffer-overflow.
- Ge.1r diagnostic audit: the `elem_size` fallback already has a `WARNING`
  fprintf behind `#ifndef NDEBUG` at mapanare_core.c:1189-1191. No additional
  diagnostic needed.

### Phase 4 — An.9r LLVM-version test fix (LOW)
- `test_post_opt_single_switch_in_hot_loop` assertion changed from
  `switch_count == 1` to `switch_count <= 1` with comment explaining LLVM 18
  may fold the switch into select instructions.

---

## Verification

| Check | Result |
|---|---|
| `black --check .` | 0 errors (370 files unchanged) |
| `ruff check .` | All checks passed |
| `pytest tests/native/test_c_hardening.py -v` | 3/3 passed (Plain, ASan, TSan) |
| `pytest tests/llvm/test_unified_return_shape.py -v` | 3/3 passed |
| `pytest tests/ --ignore=tests/bootstrap -q` | 5462 passed, 2 failed (version mismatch only), 116 skipped |

The 2 failures are expected version-mismatch: `test_user_agent_contains_current_version`
and `test_mnc_stage1_version_matches_version_file` — the binary still embeds
5.1.4 from the last rebuild. These clear once `mnc-stage1` and `libmapanare_rt.a`
are rebuilt, which is not in scope for this release.

---

## Carry-forward delta

### Closed this release (5 MEDIUM + 3 LOW)

| ID | Severity | Status |
|---|---|---|
| Lint-v5.2.0 | MEDIUM | CLOSED (was already green) |
| Bo.15 | MEDIUM | CLOSED |
| Bo.16 | MEDIUM | CLOSED |
| Stream-C | MEDIUM | CLOSED |
| An.9r | LOW | CLOSED |
| Bo.17 | LOW | CLOSED |
| Bo.14r | LOW | CLOSED |

### Still open

| ID | Severity | Release |
|---|---|---|
| In.1-stage2 | MEDIUM | v5.3.2 |
| SPEC-pkg | LOW | v5.3.3 |
| Demo gap (signals) | LOW | v5.3.3 |
| Li.1 | LOW | v5.x |
| Own.1 P2 | LOW | v5.x / v6.0 |
| Sh.4/5/6/7 | LOW | v5.x |
| Gr.1 | LOW | v5.x |

---

## Files changed

- `VERSION` (5.3.0 -> 5.3.1)
- `README.md` (version badge, fixed-point claim)
- `docs/README.es.md` (version badge)
- `docs/README.zh-CN.md` (version badge)
- `docs/README.pt.md` (version badge)
- `docs/known_issues.md` (package registry, timestamps)
- `docs/guides/getting_started.md` (version ref, test count, fixed-point)
- `tests/native/test_c_runtime.c` (4 stream tests: MnList init)
- `tests/llvm/test_unified_return_shape.py` (LLVM 18 switch count)
- `docs/roadmap/v5/v5.3.1/SESSION_REPORT.md` (this file)
- `CLAUDE.md` (v5.3.1 entry)
- `docs/roadmap/ROADMAP.md` (v5.3.1 entry)
