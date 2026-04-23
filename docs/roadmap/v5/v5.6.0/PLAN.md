# Mapanare v5.6.0 — "Sh.4: Self-Hosted Async"

> **Port `block_on` / `await` / coroutine lowering from Python bootstrap
> to `mapanare/self/`.** Closes Sh.4 (5 failing native goldens).
> Drive goldens 65/66 → ~70/66 (provisional — new tests may stay at
> 65 if v5.5.0 already closed all 11 Sh.2 tests and the 5 Sh.4 tests
> were already part of the 12-gap).

**Status:** PLANNED
**Breaking:** No (language surface unchanged; self-hosted compiler
gains support for already-spec'd syntax)
**Prerequisite:** v5.5.0 shipped (Own.1 Phase 2 closes Sh.2)
**Estimated work:** 2–3 sessions (~5–7 hours)
**Owner docket:** Sh.4 (opened v4.111.0; listed as "v5.x feature
track" since PARITY_GAPS.md:143)

---

## Why this release exists

### The failing goldens

5 goldens crash `mnc-stage1` with `Undefined function 'block_on'` per
`docs/roadmap/v4/v4.126.0/GOLDEN_TRIAGE.md`:

- `55_async_basic` — minimal `block_on { ... }` smoke test
- `56_async_await` — chained awaits
- `57_real_await` — coroutine with `.await` suspension
- `58_async_file_io` — async file I/O via coroutine
- `59_async_fanout` — spawn + join N coroutines

The Python bootstrap handles all 5. Stage1 rejects them at semantic
check:
1. `mapanare/self/semantic.mn::register_builtins` (line ~1889) doesn't
   register `block_on` or `await`.
2. Even if `block_on` were registered as a builtin, self-hosted
   `lower.mn` has no coroutine support — it would lower to an
   unresolved Call.

### Why the Python side already works

`mapanare/lower.py` recognizes `block_on { ... }` as a coroutine
wrapper, emits calls to the `__mn_coro_scheduler_*` family, and the
Python emitter wraps the block in an LLVM coroutine (`presplit`,
`@llvm.coro.id`, `@llvm.coro.save`, etc.). The C runtime
(`runtime/native/mapanare_runtime.c`) has `__mn_coro_scheduler_init/
spawn/block_on/shutdown` — all v4.150.0+ lazy-thread-aware.

The runtime is platform-complete. The missing piece is the
self-hosted compiler's *frontend* understanding of async.

### What closes when this lands

| ID | Description | Closes |
|---|---|---|
| Sh.4 | 5 goldens with `Undefined function 'block_on'` | All 5 |

If v5.5.0 closed Sh.2, v5.6.0 drives goldens 65/66 → 70/66 (if the
5 Sh.4 tests weren't counted against 65) or 65/66 → 65/66 (if the
harness already counts the 66 tests total and v5.5.0 hit 65).

**Current accounting:** the 66-total denominator already includes the
5 Sh.4 tests. At 54/66 baseline, Sh.4 accounts for 5 of the 12 gap.
After v5.5.0: 65/66 (11 Sh.2 closed). After v5.6.0: **65 + 5 = not
possible** — recount: v5.5.0 gets to 65/66 (54 + 11), meaning 1 test
still open. Then v5.6.0 cannot drive past 66/66 since max is 66.

**Corrected trajectory:**

| After | Goldens | Remaining open |
|---|---:|---|
| v5.3.2 (baseline) | 54/66 | Sh.2 (11) + Sh.4 (5) + Sh.6 (5) + Sh.7 (1) + B (1) - wait, that's 23 |

Hmm, recount: 66 - 54 = 12 open. Triage says
Sh.2 (11) + Sh.4 (5) + Sh.6 (5) + Sh.7 (1) + B (1) = **23**. That
exceeds 12, meaning some overlap or the triage is per-fix-vehicle
rather than per-test. Per `GOLDEN_TRIAGE.md:237`:

> "If categories M and B are treated as 'self-hosted compiler doesn't
> support this language feature yet' rather than regressions, the
> Sh.2 + L bucket of 14 tests is the actual self-hosted-compiler-
> regression surface."

The triage from v4.126.0 was for a 65-test corpus (not 66), and some
tests overlap categories. The authoritative count per category at
v5.3.2 baseline is out of date. The release PLAN needs a **fresh
triage** pass as Phase 0.

**Revised target:** v5.6.0 closes at least the 5 async-bucket tests
from a fresh v5.5.0-post triage. If v5.5.0 hit 65/66, v5.6.0 aims
for the remaining test (whichever async golden it is) plus any async
tests not yet counted. If v5.5.0 hit only 60/66, v5.6.0 picks up the
5 async ones explicitly.

---

## Scope

### What ships

#### 6.0a — Register async builtins in `semantic.mn`

`mapanare/self/semantic.mn::register_builtins` (line ~1889). Add:

```mapanare
register_builtin(s, "block_on", builtin_fn_type_block_on())
register_builtin(s, "await", builtin_fn_type_await())
register_builtin(s, "spawn", builtin_fn_type_spawn())
register_builtin(s, "join", builtin_fn_type_join())
```

Each `builtin_fn_type_*` helper returns a `FnType` matching the
signature the Python bootstrap already uses. Verify with
`mapanare/semantic.py` — mirror exactly, don't invent.

#### 6.0b — Coroutine expression lowering in `lower.mn`

`mapanare/self/lower.mn` — new `lower_block_on` and `lower_await`
expression handlers. Dispatch from `lower_expr` based on AST node
kind. Mirror the Python lowerer's coroutine emission pattern —
specifically, each `block_on { body }` lowers to:

1. Emit a fresh async-fn definition for `body` (the coroutine)
2. Lower the call to `__mn_coro_scheduler_spawn(fn_ptr, args)`
3. Lower the synchronous wait to `__mn_coro_scheduler_block_on(handle)`

`await expr` lowers to:

1. Call `__mn_coro_save` to mark the suspend point
2. Load the awaited future's result slot
3. Resume the coroutine on result availability

#### 6.0c — Async-aware emitter

`mapanare/self/emit_llvm.mn` — the LLVM emitter already handles user
Call nodes. The new async MIR instructions emitted by the lowerer
(likely `CoroSave`, `CoroSpawn`, `CoroBlockOn`) need emit handlers
that produce the exact LLVM intrinsic sequence the Python emitter
already writes.

Reference: `mapanare/emit_llvm_text.py` — grep for `__mn_coro_`,
`@llvm.coro.`, `presplit`. Copy the sequence, re-express in Mapanare.

**Expected LOC:**

| File | ~LOC |
|---|---:|
| `semantic.mn` — builtin registration | ~30 |
| `lower.mn` — expression handlers + MIR emission | ~200 |
| `emit_llvm.mn` — coroutine intrinsic emission | ~150 |
| **Total** | **~380** |

### What does NOT ship

- **New async syntax.** `block_on` and `await` are already spec'd.
- **Async stream combinators** (select, race, gather). Out of scope;
  v5.6.1 patch if demand appears.
- **Async `Map`/`Signal` operators.** Separate feature track.
- **Async-runtime perf work.** Perf.2 closed at v5.1.4.

---

## Exit criteria

1. 5 Sh.4 goldens compile via `mnc-stage1` without error.
2. Compiled IR passes `llvm-as`.
3. Compiled + lli-executed output matches Python bootstrap output for
   all 5 async goldens.
4. Strict 3-stage fixed-point holds.
5. Non-bootstrap pytest 0 failures.
6. `make lint` clean.
7. No new valgrind ERRORS or ASan findings on the 5 new tests.
8. `PARITY_GAPS.md` moves Sh.4 to Historical.

---

## Design decisions

### D1 — Mirror, don't reinvent

The Python bootstrap has ~2 years of coroutine emission fixes baked
in. Treat `mapanare/lower.py` + `mapanare/emit_llvm_text.py`
coroutine paths as the spec; port line-for-line where possible.

### D2 — No new MIR instruction if avoidable

If the Python lowerer lowers `block_on { body }` to a sequence of
existing MIR instructions + calls (and it does — `Call` +
`CoroSave`-as-intrinsic-name), the self-hosted lowerer should do the
same. Only add new MIR variants if strictly necessary.

### D3 — Register builtins in `register_builtins`, not inline

Other async functions may get added in v5.6.1+. Centralize the
registration.

### D4 — Tests

Reuse the 5 Sh.4 goldens as integration tests — no new
`tests/golden/*.mn` needed. Add a parser-level unit test for
`block_on { ... }` + `await` syntax in `tests/parser/`.

---

## Risks

- **R1 — LLVM coroutine intrinsic emission is finicky.** The
  `presplit` attribute, coroutine frame layout, and save/resume
  pairing have strict ordering requirements. Mitigation: run `llvm-as`
  after every helper.
- **R2 — Fixed-point breaks.** New emission in `emit_llvm.mn` changes
  stage1 binary. Mitigation: `verify_fixed_point.sh --keep` every
  rebuild.
- **R3 — Runtime mismatch.** If the self-hosted emitter writes
  slightly different calls than the C runtime expects, link fails.
  Mitigation: inspect `mapanare_runtime.c` function signatures;
  pytest coverage in `tests/runtime/`.

---

## What NOT to do

- Do not add async *syntax*. `block_on` / `await` are spec'd already.
- Do not touch the C runtime. `__mn_coro_scheduler_*` is complete.
- Do not invent new MIR instructions without checking the Python
  lowerer's emission pattern first.
- Do not run Phase 0 triage and skip updating the release target if
  v5.5.0 landed a different count than 65/66.
