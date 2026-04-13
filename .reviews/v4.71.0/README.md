# v4.71.0 Panel Summary — Arc 8: Coroutine Foundation

> 7-reviewer panel, 2026-04-13. Grades v4.67.0-v4.70.0.

## Verdict: PASS WITH NOTES (8.29/10)

Zero NEEDS WORK. Aggregate below 9.0 target but within acceptable range for
a half-shipped feature arc. **Arc 8 closes.** The coroutine foundation is
sound — Arc 9 can proceed with suspension, scheduler, and end-to-end.

## Reviewer Table

| # | Reviewer | Lens | Grade | Verdict |
|---|----------|------|-------|---------|
| 1 | Rattler | LLVM (PRIMARY) | 9/10 | PASS WITH NOTES |
| 2 | Viper | Memory safety | 8/10 | PASS WITH NOTES |
| 3 | Anaconda | Toolchain | 8/10 | PASS WITH NOTES |
| 4 | Cobra | C++/ABI | 8/10 | PASS WITH NOTES |
| 5 | Coral | Language design | 9/10 | PASS |
| 6 | Boa | Developer experience | 8/10 | PASS WITH NOTES |
| 7 | Mamba | C runtime | 8/10 | PASS WITH NOTES |

**Aggregate: 8.29/10** (58/7)

## Consensus findings

### What the arc delivered (unanimous)

1. **DESIGN.md is sound.** All 7 reviewers confirm the design document is
   thorough, the LLVM switched-resume ABI choice is correct, and the
   verification plan is realistic.
2. **Grammar + semantic layer is clean.** `async fn` / `await` syntax matches
   the design. Three semantic errors (await-outside-async, await-on-non-Future,
   forgot-to-await) are rustc-quality.
3. **Coroutine prelude IR is structurally correct.** `presplitcoroutine`
   attribute, `coro.id`/`begin`/`suspend`/`end` in correct order, cleanup
   block, Future struct allocation.
4. **41 tests across 4 test files.** Foundation is well-tested at the unit level.
5. **The "honest interim" pattern worked.** Grammar shipped first, lowering
   errors honestly, each release closes cleanly.

### Action items for Arc 9

| # | Item | Severity | Owner | Source |
|---|------|----------|-------|--------|
| 1 | Add `coro.alloc` conditional check for HALO elision path | LOW | v5.x | Rattler #3 |
| 2 | Unique GEP names for `ret.val.slot` in multi-return async fns | MEDIUM | v4.72.0 | Rattler #4 |
| 3 | Free Future struct after caller reads result | MEDIUM | v4.72.0 | Viper #1 |
| 4 | Free return value box after extraction | MEDIUM | v4.72.0 | Viper #2 |
| 5 | Full pipeline integration test (emit → llvm-as → opt → llc) | MEDIUM | v4.72.0 | Anaconda #4, Cobra #4 |
| 6 | `pending_coro_handle` field on `mapanare_agent_t` | HIGH | v4.73.0 | Mamba #3 |
| 7 | User-facing async/await documentation (cookbook/spec) | MEDIUM | v4.74.0 | Boa #3 |
| 8 | `Future.ready(x)` explicit construction | LOW | v4.73.0+ | Coral #5 |
| 9 | 8 v4.66.0 Arc 7 items still open (second panel cycle) | LOW | tracked | Boa #4 |

### What worked well

- DESIGN.md-first approach prevented the v4.19.0-v4.24.0 hollow-feature pattern
- 4-release arc pacing (design → grammar → semantic → lowering) was well-structured
- Delta review on grammar release caught nothing — the design was already validated
- The `Future<T>` type constructor integrates cleanly with the existing type system
- "Forgot to await" error is the best diagnostic in the compiler

### What needs improvement

- Testing is all string-match on IR — no integration tests against LLVM tools
- Memory leak path for Future + return value box needs explicit free
- 8 Arc 7 items continue to age without resolution
- No user documentation for async features yet
