# v5.5.5 — Scheduler-driven AwaitSuspend

> **Second real-coroutine release. Replaces v5.5.4's synchronous
> `llvm.coro.resume` drive inside `AwaitSuspend` with the real
> save/suspend/switch pattern. Outer coroutines now suspend and
> yield control back to whoever is driving them — but nothing
> drives them yet, so execution only works by virtue of the
> fast-path short-circuit (inner completes synchronously, so
> `future.state==1` by the post-drive re-check). v5.5.6 wires
> BlockOn + scheduler for the real concurrency story.**

**Status:** SHIPPED
**Breaking:** No (language surface unchanged)
**Goldens:** 59/66 unchanged; all 5 Sh.4 goldens continue to
execute correctly via fast-path short-circuit

---

## What shipped

### 5.1 — Real AwaitSuspend emission in `emit_llvm.mn`

`emit_mir_by_kind` `kind == "await_suspend"` branch (~80 LOC,
replaces ~15 lines of v5.5.4 synchronous drive). Mirrors
`emit_llvm_text.py:5305-5372` (the `_fn_is_async` branch) line
for line. Six-block pattern emitted inline:

```
; entry (current BB)
%aw.st.ptr.N = gep {i8, ptr}, ptr %future, i32 0, i32 0
%aw.st.N     = load i8, ptr %aw.st.ptr.N
%aw.rdy.N    = icmp eq i8 %aw.st.N, 1
br i1 %aw.rdy.N, label %aw.ready.N, label %aw.drive.N

aw.drive.N:
  %aw.hdl.ptr.N = gep {i8, ptr}, ptr %future, i32 0, i32 1
  %aw.hdl.N     = load ptr, ptr %aw.hdl.ptr.N
  call void @llvm.coro.resume(ptr %aw.hdl.N)
  br label %aw.check.N

aw.check.N:
  %aw.st2.N  = load i8, ptr %aw.st.ptr.N
  %aw.rdy2.N = icmp eq i8 %aw.st2.N, 1
  br i1 %aw.rdy2.N, label %aw.ready.N, label %aw.suspend.N

aw.suspend.N:
  call void @__mn_coro_register_wait(ptr %coro.hdl, ptr %future)
  %aw.save.N = call token @llvm.coro.save(ptr %coro.hdl)
  %aw.susp.N = call i8 @llvm.coro.suspend(token %aw.save.N, i1 false)
  switch i8 %aw.susp.N, label %coro.ret [
    i8 0, label %aw.resume.N
    i8 1, label %coro.cleanup
  ]

aw.resume.N:
  br label %aw.ready.N

aw.ready.N:
  %aw.val.ptr.N = gep {i8, ptr}, ptr %future, i32 0, i32 1
  %aw.val.box.N = load ptr, ptr %aw.val.ptr.N
  %aw.val.N     = load i64, ptr %aw.val.box.N
  %dest         = add i64 0, %aw.val.N
```

Tag `N` bumped once per AwaitSuspend via `st.counter`. All SSA
names use `aw.*.N` prefix (no collision with BlockOn `bo.*` or
other emission paths).

### D1 — no coro.destroy / no free in aw.ready.N

Python reference (`emit_llvm_text.py:5363-5372`) extracts the
payload and stops — no `llvm.coro.destroy`, no `@free`. This is
structurally necessary: `%aw.hdl.N` is defined only on the
`aw.drive.N` edge, so it does not dominate `aw.ready.N` when
control arrives via the fast-path or the scheduler-resume path.
Leak is preferred over a dominance violation; v5.5.7 sanitizer
hardening revisits cleanup.

### Jump targets

`%coro.hdl`, `coro.ret`, `coro.cleanup` are all set up by
v5.5.4's `emit_mir_function` prologue/epilogue. AwaitSuspend is
only emitted inside async fns (semantic guard), so these are
always in scope — no safety check needed.

---

## Verification

### IR structural — all 5 Sh.4 goldens

| Golden | llvm-as | opt -O1 | CoroSplit output |
|---|---|---|---|
| 55_async_basic | ✓ | ✓ | `@compute.resume` + `@compute.destroy` |
| 56_async_await | ✓ | ✓ | `@inner.resume`/`destroy` + **`@outer.resume`/`destroy`** |
| 57_real_await | ✓ | ✓ | fetch_a/b/c + **`@fanout.resume`/`destroy`** |
| 58_async_file_io | ✓ | ✓ | read_greeting/farewell + **`@process.resume`/`destroy`** |
| 59_async_fanout | ✓ | ✓ | 10× compute_* + **`@fanout.resume`/`destroy`** |

The **bolded** outer-fn split pairs are new at v5.5.5 — they
prove the outer coroutines really do have suspension points
now, where v5.5.4 elided them entirely.

### Execution (unexpected but welcome)

PLAN.md §R5 warned the 5 Sh.4 goldens might hang because the
outer's `coro.suspend` would yield to nothing (scheduler is
v5.5.6 work). Reality: they all still print the correct
output (42, 43, 110, done, 220, matching v5.5.4).

The reason is the **check-after-drive fast-path**: the Sh.4
goldens use async fns that return constants with no real I/O,
so when `aw.drive.N` calls `llvm.coro.resume(inner)`, the
inner runs to completion and writes `future.state=1` before
returning. `aw.check.N` then sees `state==1` and branches
straight to `aw.ready.N`, never reaching `aw.suspend.N` /
`register_wait` / `coro.suspend`. CoroSplit still generates
the suspend edge, it just never fires at runtime.

This is not a bug — v5.5.6 (scheduler-driven BlockOn) is where
the suspend path actually becomes load-bearing, and that's the
release where non-trivial async programs start working. v5.5.5
just lands the IR wiring.

### Self-hosting

| Metric | v5.5.4 | v5.5.5 | Delta |
|---|---:|---:|---:|
| stage2.ll lines | 194,052 | 194,553 | +501 (+0.26%) |
| stage2.ll `define ` count | 906 | 906 | 0 |
| stage2.ll `llvm-as` | OK | OK | — |

The +501 lines come from the `emit_line` calls in the new
AwaitSuspend handler, rendered as LLVM IR. Slightly above the
<0.1% estimate in PLAN.md §R4 but within budget.

### Tests

- **Goldens harness:** 59/66 PASS (unchanged vs v5.5.4).
- **Non-bootstrap pytest:** 5507 passed, 116 skipped, 9
  xfailed, 1 pre-existing test re-fixed (`test_user_agent`
  required `make build-rt` because the runtime archive had been
  compiled with `MAPANARE_VERSION=5.4.4`).
- **Bootstrap pytest:** 225 passed, 5 xfailed — unchanged.
- **`make lint`:** clean (ruff + black + mypy).

---

## Risk register — updated

| Risk | State | Note |
|---|---|---|
| R1 — BB count explosion | LOW-unchanged | 59's fanout has 10 awaits × 6 BBs = 60 extra BBs, no issue |
| R2 — SSA name collision | CLOSED | `aw.*.N` prefix distinct from `bo.*` and other emission paths |
| R3 — coroutine cleanup drop-glue | DEFERRED | v5.5.7 sanitizer hardening |
| R4 — fixed-point shift | LOW-realized | stage2.ll +0.26% |
| R5 — execute hangs | NOT OBSERVED | Fast-path short-circuit kept Sh.4 goldens executing; scheduler-driven suspension path still untested end-to-end — v5.5.6 exercises it |

---

## What did NOT ship (v5.5.6 scope)

- **BlockOn scheduler integration.** `emit_mir_by_kind`
  `kind == "block_on"` branch is still v5.5.4's synchronous
  `llvm.coro.resume` + payload extract.
- **`__mn_coro_scheduler_init` in main.** Needed before
  BlockOn can call `__mn_coro_scheduler_run`.
- **End-to-end test of the suspend path.** No Sh.4 golden
  actually reaches `aw.suspend.N` at runtime. Proving the
  scheduler-driven path works requires an async fn with a
  real suspension point between `coro.begin` and
  `coro.end` (e.g. a socket read that yields). That's a
  v5.5.8+ golden-corpus addition.

---

## Files changed

| File | Change |
|---|---|
| `VERSION` | 5.5.4 → 5.5.5 |
| `mapanare/self/emit_llvm.mn` | +80 / −15 (new AwaitSuspend handler) |
| `mapanare/self/mnc_all.mn` | regenerated |
| `mapanare/self/mnc-stage1` | rebuilt |
| `runtime/native/libmapanare_rt.a` | rebuilt (VERSION macro bump) |
| `docs/roadmap/v5/v5.5.5/SESSION_REPORT.md` | new |
| `CLAUDE.md` | v5.5.5 entry prepended |

---

## Commit narrative

1. `820fc11` — v5.5.5: VERSION bump (baseline preserved,
   59/66 + 42/43/110/done/220)
2. (next) — v5.5.5: scheduler-driven AwaitSuspend

## Handoff to v5.5.6

1. `emit_llvm.mn::emit_mir_by_kind` — rewrite `kind ==
   "block_on"` branch. Pattern mirrors
   `emit_llvm_text.py:5416+` (`_do_block_on`): register the
   coroutine handle, call `__mn_coro_scheduler_run()` in a
   loop until `future.state == 1`, then extract payload.
2. Inject `__mn_coro_scheduler_init` into main's entry BB
   (or lazily on first BlockOn — Python does the latter).
3. Re-verify Sh.4 goldens: the expected behavior remains
   42/43/110/done/220, but now the scheduler path is
   load-bearing for multi-future or truly-async goldens
   added in v5.5.8+.
4. No runtime changes expected — `__mn_coro_scheduler_*` API
   complete since v5.1.4.
