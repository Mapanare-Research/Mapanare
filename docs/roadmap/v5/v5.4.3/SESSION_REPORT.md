# v5.4.3 Session Report — Close Rt.03 (loop-reassignment)

**Date:** 2026-04-23
**Status:** READY TO TAG
**Scope:** Add loop-depth tracking to both emitters and prepend a
free-before-store to `emit_track_string` / `_boxed` / `_closure`
(self-hosted) and `_track_string` / `_track_boxed` / `_track_closure`
(Python) when the emit site is inside a for / while body. Closes
Rt.03 (22_string_builder) that v5.4.2 baseline-gated.

## Starting state (v5.4.2 tag)

- Version: 5.4.2
- Native goldens: 54/66 PASS
- Valgrind: 66 WARNINGS_ONLY / 0 ERRORS
- ASan UAF/overflow: 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR
- ASan leak sweep: 44 CLEAN / 4 LEAK (baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL
- stage2.ll: 168952 lines; `llvm-as` OK; stage3.ll empty (Ve.1)
- Rt.03 baseline-gated in `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`

## Phase-by-phase

### Phase 0 — VERSION bump + baseline confirm

`VERSION` 5.4.2 → 5.4.3. `make leak-check` PASS, goldens 54/66.

### Phase 1 — loop_depth counter (plumbing only)

`EmitState` gains `loop_depth: Int` (18 → 19 fields). Registry bumped
in both `build_internal_struct_list` and `register_all_internal_structs`.
Reset to 0 at `emit_mir_function` entry alongside the other per-fn
owner-list resets.

Push/pop sites: `emit_mir_basic_block` increments when `bb.label` starts
with `for_body` / `while_body` / `mapfor_body`, decrements before
returning (matched on the bumped flag so the pop only fires when the
push did — the early-return branch also pops correctly).

Python `LLVMTextEmitter._loop_depth: int`: reset in `_emit_fn`, push/pop
around the `for bb in fn.blocks` loop using the same block-label
prefix check via `str.startswith`.

No IR-shape change yet (pure plumbing). Goldens 54/66 preserved.

### Phase 2 — free-before-store

`emit_track_string` (self-hosted): when `s.loop_depth > 0`, prepend

```llvm
%prev.str.N = load {ptr, i64}, ptr %str_track.N
call void @__mn_str_free({ptr, i64} %prev.str.N)
```

before the existing `store {ptr, i64} %val, ptr %str_track.N` line.
Identical shape for `emit_track_boxed` (ptr + `@free`).
`emit_track_closure` routes through `emit_track_boxed` so the guard
inherits automatically.

Python parity: `_track_string` / `_track_boxed` / `_track_closure` gain
the same loop-depth guard. Closure free extracts `extractvalue ...  , 1`
(the env_ptr; the fn_ptr is code). `@__mn_str_free` / `@free` / runtime
null-tolerance make the first-iteration free a no-op — zero-init in the
entry-block prelude + null-safe runtime frees combine to make this safe
without a runtime branch.

The aliased-copy UAF risk from PLAN.md §D3 did not materialize on the
current corpus: the UAF sweep stayed byte-identical (55 CLEAN / 0
ASAN_ERROR / 11 CRASH_NO_ASAN). The self-hosted compiler's String
patterns (forward-propagating state threads, not captured aliases
across mutations) hold up under the fix.

### Phase 3 — Sanitizer HARD GATE

After every commit:

| Metric | v5.4.2 | v5.4.3 |
|---|---|---|
| Goldens | 54/66 | 54/66 |
| ASan UAF/overflow | 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR | 55 CLEAN / 11 CRASH_NO_ASAN / 0 ASAN_ERROR |
| ASan leak sweep | 44 CLEAN / 4 LEAK | **45 CLEAN / 3 LEAK** |
| Valgrind | 66 WARNINGS_ONLY / 0 ERRORS | 66 WARNINGS_ONLY / 0 ERRORS |
| 22_string_builder | 6 objs / 19 B | **CLEAN** |
| stage2.ll | 168952 lines | **169280 lines** (+0.19%) |
| stage2 `llvm-as` | OK | OK |
| stage3 | empty (Ve.1 preserved) | empty (Ve.1 preserved) |

R3 stage2.ll budget: +0.19% vs +5% ceiling — well under.

### Phase 4 — baseline refresh

`docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv` updated: the
22_string_builder row becomes `0 0 0 0 - CLEAN`. `make leak-check` now
treats any regression back to leaking that golden as CI fail. Fresh
post-fix snapshot at `docs/roadmap/v5/v5.4.3/asan-leak-summary-post-fix.tsv`.

`docs/known_issues.md` Rt.03 row flipped to `**CLOSED v5.4.3**` with
the verification note.

### Phase 5 — final sanitizer gate

- UAF sweep: 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN (byte-identical).
- Leak sweep: PASS vs refreshed baseline.
- Valgrind: 66 WARNINGS_ONLY / 0 ERRORS.
- Fixed point: stage2.ll OK, stage3 empty (Ve.1 preserved, matches v5.4.2).

### Phase 6 — pytest + lint

- `make build-rt` with `MAPANARE_VERSION=5.4.3`.
- `python3 -m pytest tests/ --ignore=tests/bootstrap -q`:
  **5494 passed / 0 failed / 116 skipped / 9 xfailed** (480s).
- `make lint`: clean.
- Goldens: 54/66 preserved.
- `make leak-check`: PASS vs refreshed baseline.

### Phase 7 — release artifacts

- `SESSION_REPORT.md` (this file).
- `docs/roadmap/v5/v5.4.3/asan-leak-summary-post-fix.tsv` saved.
- `docs/roadmap/ROADMAP.md`: v5.4.3 entry.
- `CLAUDE.md`: v5.4.3 prepended to recent-6; v5.3.1 drops off.
- `PARITY_GAPS.md`: Own.1 Phase 2 row appended
  `+ loop-reassignment-clean`.
- `docs/known_issues.md`: Rt.03 CLOSED v5.4.3.

## Final state

- Version: 5.4.3
- Native goldens: 54/66 PASS (unchanged)
- Valgrind: 66 WARNINGS_ONLY / 0 ERRORS
- ASan UAF/overflow: 55 CLEAN / 0 ASAN_ERROR / 11 CRASH_NO_ASAN
- ASan leak sweep: 45 CLEAN / 3 LEAK (Rt.02 × 2 + Rt.04, baseline-gated) / 11 COMPILE_FAIL / 7 LINK_FAIL / 0 RUN_FAIL
- stage2.ll: 169280 lines; `llvm-as` OK; stage3.ll empty (Ve.1 preserved)
- Non-bootstrap pytest: 5494 passed / 0 failed
- `make lint`: clean
- `make leak-check`: PASS (0 regressions vs refreshed baseline)

## Deviations from PLAN.md

None. D3 UAF risk didn't materialize — the planned HARD-GATE-and-revert
path was exercised but the fix passed cleanly.

## Commit history

```
cd4defa v5.4.3 Phase 4: refresh leak baseline — 22_string_builder CLEAN
27a9888 v5.4.3 Phase 2: free-before-store in tracking helpers when loop_depth > 0
6bfb595 v5.4.3 Phase 1: loop_depth counter in both emitters (plumbing only)
284282e v5.4.3: version bump — close Rt.03 loop-reassignment
```

## What v5.4.3 opens

- **v5.4.4 Rt.04** — struct-return intermediates (62_list_output).
  One-level struct-field walk in drop-glue: extract every ptr-typed
  field from struct-return aggregates and add to per-resource ret-ptr
  comparison lists. Removes v5.4.1 Phase 4's conservative
  skip-all-drops guard.
