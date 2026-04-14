# Mapanare v4.113.0 — Coroutine Frame Decoupling + Medium Items

> **Phase D release 3.** Close the remaining medium and low docket items
> from the v4.99.0 panel. Docket #8: `mn_coro_is_done` reads a hardcoded
> offset into the coroutine frame — replace with a stable API. Docket #10:
> keyword collision space is undocumented in the SPEC. Docket #11: async
> error messages are unhelpful. This release closes all three and preps
> for the Phase D panel at v4.114.0.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.112.0
**Delta review:** No
**Full panel:** No (v4.114.0)
**Estimated work:** 1 sprint
**Theme:** Close the remaining v4.99.0 docket items — coroutine frame stability, SPEC completeness, error quality.

---

## Scope

The v4.99.0 panel identified 11 docket items. Phase A (v4.100.0-v4.103.0)
closed the 5 critical/high items (#1-#5). v4.112.0 closed #7 (byref size
heuristic). This release closes the remaining three Mapanare-owned items:

**Docket #8 (MEDIUM)** — Coroutine frame layout coupling. Viper flagged
this: `mn_coro_is_done` in the C runtime reads a hardcoded byte offset
into the coroutine frame struct to check completion status. If the frame
layout changes (new fields, reordering), the offset silently breaks.
The fix: either add an `int8_t status` field at a fixed position (offset
0) in the coroutine frame, or replace the manual offset read with LLVM's
`llvm.coro.done` intrinsic.

**Docket #10 (LOW)** — Keyword collision space. Mapanare has bilingual
keywords (English + Spanish: `fn`/`funcion`, `if`/`si`, `else`/`sino`,
etc.). The SPEC does not document the full keyword table or explain that
these tokens cannot be used as identifiers. Write the SPEC section.

**Docket #11 (LOW)** — Async error messages. When an async operation
fails (spawn fails, channel send to closed receiver, await on dropped
future), the error messages are generic ("runtime error") instead of
explaining the async-specific cause. Improve the messages.

After v4.113.0, every docket item from the v4.99.0 panel is either CLOSED
or ACCEPTED (item #6 was documentation, addressed in Phase C; item #10
was string concat performance, investigated in Phase C).

## Phase 1 — Fix docket #8: coroutine frame decoupling

- [ ] Read `runtime/native/mapanare_runtime.c` — find `mn_coro_is_done` and the coroutine frame struct
- [ ] Identify the hardcoded offset: which byte offset is read? What field does it correspond to?
- [ ] Evaluate fix options:
  - **Option A**: Add `int8_t status` at offset 0 (before all other fields) in the coroutine frame struct. Update `mn_coro_is_done` to read `frame->status`. This is a layout guarantee — status is always at offset 0.
  - **Option B**: Use LLVM's `llvm.coro.done` intrinsic instead of manual frame inspection. This delegates the layout to LLVM entirely.
- [ ] Implement the chosen fix
- [ ] Update `mapanare/emit_llvm_text.py` if coroutine frame IR generation references the old layout
- [ ] Update `mapanare/self/emit_llvm.mn` if the self-hosted emitter generates coroutine frames
- [ ] Remove all hardcoded numeric offsets into the coroutine frame from the codebase
- [ ] Grep for any other hardcoded frame offsets (e.g., in `mapanare_agent.c`, scheduler code)

## Phase 2 — Verify async golden tests

- [ ] Run async golden tests (55-57) through the native pipeline:
  - `tests/golden/55_async_await.mn`
  - `tests/golden/56_async_channels.mn`
  - `tests/golden/57_async_spawn.mn`
- [ ] Compile each through mnc-stage1, link with `libmapanare_rt.a`, run natively
- [ ] Verify output matches expected results
- [ ] Run valgrind on each async test: `valgrind --leak-check=full ./test_binary`
- [ ] If any test fails, investigate whether the coroutine frame change caused the regression

## Phase 3 — Fix docket #10: keyword collision SPEC section

- [ ] Read `docs/SPEC.md` — find the lexical grammar section (or equivalent)
- [ ] Write a new section: "Reserved Keywords"
  - Table of all keywords with English and Spanish forms
  - Statement that all reserved keywords cannot be used as identifiers
  - Note on case sensitivity
  - Cross-reference with the grammar in `mapanare/mapanare.lark`
- [ ] Verify the keyword table matches the actual lexer:
  - Check `mapanare/parser.py` or `mapanare/mapanare.lark` for the authoritative keyword list
  - Check `mapanare/self/lexer.mn` for the self-hosted keyword list
  - Flag any discrepancies between the two

## Phase 4 — Fix docket #11: async error messages

- [ ] Grep for generic error messages in async/coroutine code paths:
  - `runtime/native/mapanare_runtime.c` — scheduler, coroutine, channel error paths
  - `mapanare/emit_llvm_text.py` — emitted error handling in async functions
- [ ] Replace generic messages with specific ones:
  - Spawn failure: "failed to spawn async task: {reason}" (thread pool exhausted, invalid function, etc.)
  - Channel send to closed: "cannot send to channel: receiver has been dropped"
  - Await on dropped future: "cannot await: the producing task was cancelled or dropped"
  - Timeout: "async operation timed out after {N}ms"
- [ ] Add at least 3 improved error messages across different async failure modes
- [ ] Verify the messages appear: write a test or manually trigger each failure mode

## Phase 5 — Full test suite + integration

- [ ] `make test` — full pytest suite
- [ ] `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v` — all 64 golden
- [ ] Verify no regressions from v4.112.0
- [ ] Run `python scripts/ir_doctor.py stage2` — stage2 still validates
- [ ] Rebuild self-hosted: `bash scripts/rebuild.sh` — no build failures from the changes

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.113.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Coroutine frame decoupled — no hardcoded byte offsets | diff of runtime + grep confirms no numeric offsets |
| 2 | `mn_coro_is_done` uses stable API (field access or intrinsic) | diff of `mapanare_runtime.c` |
| 3 | Async golden tests (55-57) pass natively | test output |
| 4 | Valgrind clean on async golden tests | valgrind output |
| 5 | SPEC "Reserved Keywords" section written | diff of `docs/SPEC.md` |
| 6 | Keyword table matches actual lexer (both pipelines) | cross-reference audit |
| 7 | At least 3 async error messages improved | diff of error-producing files |
| 8 | Full golden suite: no regression from v4.112.0 | test log |
| 9 | Stage2 validates | `ir_doctor.py stage2` output |

---

## What this release does NOT do

- **Run a panel** — the Phase D panel is v4.114.0.
- **Fix remaining fixed-point divergences** — non-byref divergences documented in v4.112.0 are future work.
- **Add new async features** — this is a fix/polish release for existing async infrastructure.
- **Rewrite the coroutine implementation** — the fix is minimal: remove hardcoded offsets, add a stable field or use an intrinsic. The coroutine architecture is unchanged.
- **Address docket #6 (README disclosure)** or **#9 (string concat perf)** — both were addressed in Phase C.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Coroutine frame layout change breaks existing async tests | medium | high | Run all 3 async golden tests + valgrind after the fix. If any break, revert and debug. |
| LLVM `llvm.coro.done` intrinsic not available in target LLVM version | low | high | Fall back to Option A (fixed-offset status field). Check LLVM version in build scripts. |
| Keyword table in SPEC diverges from actual lexer | low | medium | Cross-reference both `mapanare.lark` and `lexer.mn`. Fix discrepancies in the lexers, not in the SPEC. |
| Improved error messages are unreachable in practice | medium | low | Manually trigger each failure mode to verify the message appears. If a path is unreachable, note it. |
| Coroutine frame change affects the self-hosted emitter's output | low | medium | Check if `emit_llvm.mn` generates coroutine-related IR. If so, update it to match the new layout. |

---

## After v4.113.0

v4.114.0 is the Phase D panel. Seven reviewers grade v4.111.0-v4.113.0: self-hosted golden parity, fixed-point convergence, docket closure. Key questions: does the self-hosted compiler produce correct IR? Is the fixed-point real? Are docket items #7, #8, #10, #11 genuinely closed? If PASS, proceed to Phase E (polish). If NEEDS WORK, patch release.
