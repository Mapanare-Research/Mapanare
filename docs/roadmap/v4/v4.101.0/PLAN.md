# Mapanare v4.101.0 — Fix List Indexing Bug

> **Phase A release 2.** With the tagged-pointer UB fixed in v4.100.0,
> the native binary produces correct string output. The next blocker is
> the list indexing bug (v4.99.0 docket item #2, CRITICAL): `data[j]`
> returns garbage in certain code contexts despite working correctly in
> quicksort. This release reproduces, diagnoses, and fixes the root
> cause.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.100.0
**Delta review:** No
**Full panel:** No (v4.106.0)
**Estimated work:** 1 sprint
**Theme:** Fix list element access returning garbage — the second critical bug from the v4.99.0 docket.

---

## Scope

The v4.99.0 panel identified list indexing as a CRITICAL bug: `data[j]` returns garbage values in certain contexts while working correctly in others (e.g., quicksort). This inconsistency points to a codegen bug in the emitter — the IR generated for list element access differs depending on context (function nesting, variable scope, optimization level, or surrounding code patterns).

The approach: reproduce the bug with a minimal .mn program, compare the IR generated for working and broken list access, identify the divergence (likely a GEP with wrong indices, a load with wrong type, or a missing dereference), fix the emitter, and add a regression test.

With v4.100.0 fixing the tagged-pointer UB, we can now trust the native binary's output enough to isolate this bug. Before v4.100.0, garbled strings masked all other failures.

## Phase 1 — Reproduce the bug

- [ ] Review the v4.99.0 panel notes — identify which specific test or benchmark exhibits the list indexing failure
- [ ] Search existing golden tests for list-heavy programs — identify which ones pass and which ones produce garbage
- [ ] Create a minimal reproducer: `tests/golden/62_list_indexing.mn`
  - Include at minimum: list creation, element access by variable index, element access in a loop, element access after list mutation
  - Include the specific pattern that fails (from the panel's description)
- [ ] Compile the reproducer through the Python bootstrap — verify it produces correct output
- [ ] Compile the reproducer through mnc-stage1 — verify it produces garbage (confirming the bug)

## Phase 2 — Trace the emitter divergence

- [ ] Emit LLVM IR for the reproducer: `python -m mapanare emit-llvm tests/golden/62_list_indexing.mn`
- [ ] Emit LLVM IR from mnc-stage1 for the same file (if supported) or inspect the IR that the quicksort golden test generates for its list access
- [ ] Compare the IR generated for working list access (quicksort) vs broken list access (reproducer):
  - Focus on GEP instructions targeting list data
  - Focus on load instructions reading list elements
  - Focus on the list struct layout assumed by each access pattern
- [ ] Identify the divergence — document the root cause:
  - Wrong GEP index (off-by-one, wrong field)?
  - Wrong load type (i64 vs ptr vs i8)?
  - Missing dereference (loading the list struct instead of the element)?
  - Pointer-to-pointer confusion?

## Phase 3 — Fix the emitter

- [ ] Fix the root cause in `mapanare/emit_llvm_text.py`
- [ ] If the bug also exists in `mapanare/self/emit_llvm.mn`, fix it there too
- [ ] If the bug is in `mapanare/lower.py` (wrong MIR generated for list access), fix at the MIR level
- [ ] Verify the fix does not break quicksort or other working list access patterns
- [ ] Re-emit IR for the reproducer — confirm the GEP/load now matches the working pattern

## Phase 4 — Regression test

- [ ] Finalize `tests/golden/62_list_indexing.mn` with comprehensive coverage:
  - List literal construction
  - Access by literal index: `data[0]`, `data[2]`
  - Access by variable index: `let i = 1; data[i]`
  - Access in a for loop: `for i in range(len(data))`
  - Access after push/append
  - Nested list access (if applicable): `data[i][j]`
  - List passed as function argument, accessed inside
- [ ] Add corresponding pytest: `tests/llvm/test_list_indexing.py` (or add cases to existing list test file)
- [ ] Verify the golden test passes through both Python bootstrap and mnc-stage1

## Phase 5 — Rebuild + full golden suite

- [ ] Rebuild mnc-stage1: `python scripts/build_stage1.py`
- [ ] Run all golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Target: 62/62 (61 existing + 1 new `62_list_indexing.mn`)
- [ ] Record pass count — any failures should be unrelated to list indexing

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.101.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Bug reproduced: minimal .mn file shows garbage from list access | reproducer output |
| 2 | Root cause identified and documented | SESSION_REPORT.md root cause section |
| 3 | Fix applied in emitter (`emit_llvm_text.py` and/or `emit_llvm.mn`) | diff |
| 4 | Regression test: `tests/golden/62_list_indexing.mn` | file exists, passes both pipelines |
| 5 | Quicksort and other existing list tests still pass | no regressions |
| 6 | 62/62 golden tests pass through mnc-stage1 | test log |
| 7 | pytest integration tests pass | `make test` output |
| 8 | Root cause does not affect C backend (`emit_c.py`) or is fixed there too | audit |

---

## What this release does NOT do

- **Fix async linking** — that is v4.102.0.
- **Fix else/sino or closure types** — that is v4.103.0.
- **Optimize list performance** — this fixes correctness, not speed.
- **Change list implementation** — the Robin Hood hash table for maps and the dynamic array for lists are unchanged. Only the codegen for element access is fixed.
- **Run a panel** — Phase A has no panel. The next panel is v4.106.0.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Root cause is in MIR lowering, not the emitter — fix is deeper than expected | medium | medium | Phase 2 traces from IR back to MIR; if the MIR is wrong, fix `lower.py` |
| Fix breaks quicksort or other working list access patterns | low | high | Run ALL golden tests after the fix; quicksort is the first regression check |
| Bug is actually in the C runtime list implementation, not the emitter | low | medium | Phase 2 IR comparison will reveal whether the issue is codegen or runtime |
| Minimal reproducer does not trigger the bug (it is context-dependent) | medium | medium | Use the exact code pattern from the panel report; try multiple contexts |
| Self-hosted emitter (`emit_llvm.mn`) has a different root cause than Python emitter | medium | medium | Fix both independently; verify both produce correct IR for the reproducer |

---

## After v4.101.0

v4.102.0 fixes async linking (docket item #3) and runs async programs natively for the first time. `__mn_coro_scheduler_*` functions are not exported to `libmapanare_rt.a` — a build system fix. After v4.102.0, three of the five critical/high docket items will be closed.
