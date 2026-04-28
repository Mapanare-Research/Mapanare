# v5.5.0 — Sh.4 Phase 1: semantic builtins for async

> **Micro-release split of v5.5.0.** The original monolithic
> v5.5.0 plan (register builtins + lower + emit + close Sh.4)
> was re-scoped into three micro-releases:
>
> - **v5.5.0** (this release) — Phase 1 only: register `block_on`
>   in `semantic.mn`. Async goldens advance past semantic but
>   still produce unlinkable IR (undeclared `@block_on`). Harness
>   PASS count ticks up because the harness checks function-count
>   parity, not IR validity.
> - **v5.5.1** — Phase 2: `BlockOn`/`AwaitSuspend` MIR variants +
>   lowerer; `async` decorator propagates to `Fn.is_async`.
> - **v5.5.2** — Phase 3+: coroutine intrinsic emission, scheduler
>   init, sanitizer sweep; real Sh.4 close.

**Status:** SHIPPED
**Breaking:** No (language surface unchanged)
**Goldens:** 54/66 → **59/66** (harness PASS; +5 Sh.4 at
function-count parity only — execution correctness pending
v5.5.2)

---

## What shipped

### semantic.mn (3 surgical edits)

- `is_builtin_function(name)` — added `block_on` branch.
- `builtin_return_type(name)` — added `block_on` → `"<unknown>"`
  (type-inferred at call site from the awaited `Future<T>`).
- `register_builtins(st)` — added `block_on` symbol with
  `make_builtin_fn_type(unknown_type())`.
- `infer_expr` — added explicit `"await"` case that recurses into
  the inner expression so errors inside `await foo()` are caught,
  returning `unknown_type()` for the outer await.

Total: +17 lines, 0 deletions.

### What this unblocks

Before v5.5.0, `mnc-stage1` rejected all 5 Sh.4 goldens at
semantic with `error: Undefined function 'block_on'`. After
v5.5.0, stage1 lowers through lower.mn + emit_llvm.mn, producing
IR that contains an undeclared `call i64 @block_on(...)`. The
test harness `scripts/test_native.py` compares stage1 against the
Python bootstrap by **function-count / function-name set**, not
by IR validity — so it flips PASS even though `llvm-as` rejects
the IR.

v5.5.1 wires the lowerer to emit `BlockOn` / `AwaitSuspend` MIR.
v5.5.2 wires the emitter to produce the coroutine intrinsic
sequence the runtime already expects.

### What explicitly did NOT ship

- `spawn` / `join` builtin registration — not exercised by the 5
  Sh.4 goldens (55_async_basic through 59_async_fanout only use
  `block_on` + `await`). Deferred to v5.5.1+ when their MIR
  variants land.
- Any lower.mn changes.
- Any emit_llvm.mn changes.
- Any MIR changes.
- Any runtime changes.

---

## Exit criteria status

| # | Criterion | v5.5.0 | v5.5.1 | v5.5.2 |
|---|---|:---:|:---:|:---:|
| 1 | 5 Sh.4 goldens compile via mnc-stage1 | ✅ harness PASS | — | — |
| 2 | Compiled IR passes `llvm-as` | ❌ undeclared `@block_on` | — | ✅ |
| 3 | lli-executed output matches bootstrap | ❌ | ❌ | ✅ |
| 4 | Fixed-point NEAR/STRICT | TBD | — | — |
| 5 | Non-bootstrap pytest 0 failures | N/A (only .mn files touched) | — | — |
| 6 | `make lint` clean | N/A (only .mn files touched) | — | — |
| 7 | No new valgrind/ASan on Sh.4 tests | N/A (tests don't execute) | — | ✅ |
| 8 | PARITY_GAPS.md Sh.4 → Historical | — | — | ✅ |

---

## Risk assessment

**Low.** Only `mapanare/self/semantic.mn` touched, and only
additively (no existing branches modified). The self-hosted
compiler compiling itself is unaffected — the 17 new lines are
dead code for all non-async inputs, and `mnc_all.mn` contains no
async code. Stage1 rebuild succeeded; goldens went 54 → 59 with
no regressions in the previously-passing 54 (the 7 remaining
failures are the known Sh.6 tensor / Sh.7 closure / B
bootstrap-fail categories, unchanged).

Fixed-point verification deferred to v5.5.1 when more substantive
changes land. Phase 1's surface is small enough that a
conservative fixed-point audit isn't the risk-reduction priority.

---

## Migration note for v5.5.1

Next release adds:

1. `BlockOn(dest, future)` + `AwaitSuspend(dest, future)` MIR
   variants in `mapanare/self/mir.mn` (mirror `mapanare/mir.py`
   lines 720–748).
2. `Fn.is_async: Bool` field on MIR Fn (propagated from the
   `"async"` decorator the self-hosted parser already stashes per
   `mapanare/self/parser.mn:797–798`).
3. `lower_block_on` / `lower_await` dispatch in
   `mapanare/self/lower.mn::lower_call` — mirror
   `mapanare/lower.py:1836–1856`.

The emitter stays untouched until v5.5.2.

---

## Commits

- `VERSION`: 5.4.4 → 5.5.0
- `mapanare/self/semantic.mn`: +17 lines (3 edits)
- `docs/roadmap/v5/v5.5.0/SESSION_REPORT.md`: this file
- Recompiled artifacts: `main.ll`, `main.o`, `mnc-stage1`, etc.
