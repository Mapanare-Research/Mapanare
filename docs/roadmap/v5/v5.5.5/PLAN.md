# Mapanare v5.5.5 — "Scheduler-driven AwaitSuspend"

> **Second real-coroutine release. Replaces v5.5.4's synchronous
> `llvm.coro.resume` drive inside `AwaitSuspend` emission with
> the real save/suspend/switch pattern that yields control back
> to the scheduler. Prerequisite to v5.5.6 (scheduler-driven
> BlockOn + main lifecycle) — only after v5.5.6 does concurrency
> actually kick in, but the IR wiring must land here first.**

**Status:** PLANNED
**Breaking:** No (language surface unchanged)
**Prerequisite:** v5.5.4 shipped (real coroutine prologue/epilogue)
**Estimated work:** 1 session (~2–3 hours)

---

## Why this release exists

### v5.5.4 leftover

v5.5.4's `AwaitSuspend` emission (`emit_llvm.mn`,
`emit_mir_by_kind` branch):

```
; AwaitSuspend(%dest, %future) — v5.5.4 synchronous drive
%aw.hdl.ptr.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
%aw.hdl.N     = load ptr, ptr %aw.hdl.ptr.N
call void @llvm.coro.resume(ptr %aw.hdl.N)   ; INLINE RESUME
%aw.val.ptr.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
%aw.val.box.N = load ptr, ptr %aw.val.ptr.N
%aw.val.N     = load i64, ptr %aw.val.box.N
%dest         = add i64 0, %aw.val.N
call void @llvm.coro.destroy(ptr %aw.hdl.N)
...
```

The inline `call void @llvm.coro.resume` drives the inner
coroutine to completion **right there** on the current thread,
blocking the outer coroutine. No suspension, no scheduler
involvement, no chance for other tasks to progress.

### What v5.5.5 changes

Replace the inline resume with the real pattern from
`emit_llvm_text.py:5291–5414`:

1. **Fast-path readiness check.** Load `future.state` — if
   already 1 (Ready), skip straight to the extract block.
   Saves a scheduler round-trip when the awaited future is
   trivially complete.
2. **Drive once.** `llvm.coro.resume(inner.hdl)` to start the
   inner coroutine running. After resume returns, re-check
   `future.state`.
3. **Still not ready? Register + suspend outer.**
   `__mn_coro_register_wait(%coro.hdl, %future)` tells the
   scheduler "resume me when `%future` becomes Ready".
   Then the outer's own `llvm.coro.save` + `llvm.coro.suspend`
   + `switch` yields control back to whoever is driving this
   outer coroutine (BlockOn's scheduler_run, in v5.5.6+).
4. **Resume path.** When the scheduler resumes us, the future
   is guaranteed Ready. Fall through to extract.
5. **Extract.** GEP + load payload → load T.

### Why v5.5.5 lands BEFORE v5.5.6

The IR pattern in §1.2 uses `%coro.hdl` inside the outer
async fn's body. That's only defined when the outer IS an
async fn — set up in the v5.5.4 coro.entry prologue.

`AwaitSuspend` is only emitted inside async fn bodies
(semantic check: await is only valid in async context). So
`%coro.hdl` is always defined at the AwaitSuspend emission
point — no safety check needed.

`BlockOn` is the opposite — it's called from non-async
context (typically main). No `%coro.hdl` available. That's
why BlockOn scheduler integration is v5.5.6's job, not
v5.5.5's.

---

## Scope

### What ships

#### 5.1 — Real `AwaitSuspend` emission

`emit_llvm.mn::emit_mir_by_kind` (the `kind == "await_suspend"`
branch). Replace the v5.5.4 synchronous pattern with:

```
; AwaitSuspend(%dest, %future)
; Fast-path readiness check
%aw.st.ptr.N  = gep {i8,ptr}, ptr %future, i32 0, i32 0
%aw.st.N      = load i8, ptr %aw.st.ptr.N
%aw.rdy.N     = icmp eq i8 %aw.st.N, 1
br i1 %aw.rdy.N, label %aw.ready.N, label %aw.drive.N

aw.drive.N:
; Drive the inner coroutine once.
%aw.hdl.ptr.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
%aw.hdl.N     = load ptr, ptr %aw.hdl.ptr.N
call void @llvm.coro.resume(ptr %aw.hdl.N)
br label %aw.check.N

aw.check.N:
; Re-check readiness after the inner ran.
%aw.st2.N     = load i8, ptr %aw.st.ptr.N
%aw.rdy2.N    = icmp eq i8 %aw.st2.N, 1
br i1 %aw.rdy2.N, label %aw.ready.N, label %aw.suspend.N

aw.suspend.N:
; Register wait + suspend OUTER coroutine.
call void @__mn_coro_register_wait(ptr %coro.hdl, ptr %future)
%aw.save.N    = call token @llvm.coro.save(ptr %coro.hdl)
%aw.susp.N    = call i8 @llvm.coro.suspend(token %aw.save.N, i1 false)
switch i8 %aw.susp.N, label %coro.ret [
  i8 0, label %aw.resume.N
  i8 1, label %coro.cleanup
]

aw.resume.N:
; Scheduler resumed us — future IS Ready now.
br label %aw.ready.N

aw.ready.N:
; Extract value.
%aw.val.ptr.N = gep {i8,ptr}, ptr %future, i32 0, i32 1
%aw.val.box.N = load ptr, ptr %aw.val.ptr.N
%aw.val.N     = load i64, ptr %aw.val.box.N
%dest         = add i64 0, %aw.val.N
call void @llvm.coro.destroy(ptr %aw.hdl.N)   ; handle from aw.drive.N
call void @free(ptr %aw.val.box.N)
call void @free(ptr %future)
```

**Expected LOC:** ~80 in `emit_llvm.mn` (replaces ~15 existing
synchronous-drive lines).

### What does NOT ship

- **BlockOn scheduler integration.** v5.5.6.
- **main() `__mn_coro_scheduler_init` call.** v5.5.6 — v5.5.5
  alone produces IR that calls `register_wait` but nothing
  calls `scheduler_run`, so the outer's suspend never returns.
  **This means v5.5.5's IR doesn't execute correctly on its
  own.** v5.5.5 + v5.5.6 must ship before async goldens are
  re-run.

### Runtime interaction

No runtime changes. The scheduler API
(`__mn_coro_register_wait`) is already complete and TSan-clean
since v5.1.4.

---

## Exit criteria

**Note: v5.5.5 is a partial wiring release.** The async
goldens **cannot execute correctly** after v5.5.5 alone —
outer coroutines will suspend and never be resumed (no
scheduler_run). That's fine, it's the handoff contract with
v5.5.6.

1. Stage1 rebuilds successfully.
2. 5 Sh.4 goldens compile, `llvm-as` clean, **but may hang or
   crash on execution** (awaited-block-forever). Documented.
3. `opt -O1` still clean (IR still valid pre-split).
4. Post-opt CoroSplit produces `@outer.resume` /
   `@outer.destroy` (outer fns now really have suspend points).
5. stage2.ll: llvm-as clean, self-hosting preserved
   (mnc-stage1 compiles mnc_all.mn without error).
6. Non-bootstrap pytest 0 failures.
7. `make lint` clean.
8. Goldens harness still at 59/66 (test_native.py checks
   function counts, not execution).

---

## Design decisions

### D1 — Fast-path readiness check

Python does it (`emit_llvm_text.py:5319–5322`). Keep. Most
awaited futures are already-ready in practice (tight coroutine
chains without real I/O between). Skipping the scheduler
round-trip in the common case is free perf.

### D2 — Basic block count per await

6 new BBs: `aw.drive.N`, `aw.check.N`, `aw.suspend.N`,
`aw.resume.N`, `aw.ready.N`, plus the implicit entry (which
is the BB emit_mir_by_kind is already in).

Tag counter `N` uses `st.counter` (shared with other
emission paths). Increment once per AwaitSuspend instance.

### D3 — Block emission via emit_line (not emit_mir_basic_block)

The 6 BBs are synthetic — emitted directly via
`emit_line(s, "<label>:")` and subsequent `emit_line` for
instructions. They don't go through `emit_mir_basic_block`
(which would want a MIR `BasicBlock` struct).

**Caveat:** Entry-block buffering (`entry_block_body` field,
v5.4.1) is still active during this emission. All lines land
in the body buffer. That's correct — the 6 BBs need to appear
inside the function, after the user's async fn body, before
the coro.final/cleanup/ret epilogue.

### D4 — No separate "already had `coro.hdl` defined" check

`%coro.hdl` is always defined at AwaitSuspend emission point
because `AwaitSuspend` is only emitted inside async fns (which
always have the v5.5.4 coro.entry prologue). Semantic check
enforces this. Trust.

### D5 — coro.cleanup jump target

The `switch` after `coro.suspend` has three labels:
- `coro.ret` (default — destroyed-at-suspend, rare)
- `aw.resume.N` (i8 0 — normal resume)
- `coro.cleanup` (i8 1 — caller destroys us at the suspend
  point, common on cancel)

`coro.cleanup` and `coro.ret` are always defined in the outer's
epilogue (emitted by v5.5.4's emit_mir_function). Trust.

---

## Risks

### R1 — Outer fn ends up with too many basic blocks (LOW)

Each await adds 6 BBs. An async fn with 10 awaits adds 60
BBs. LLVM's CoroSplit handles arbitrary block counts fine.

### R2 — SSA name collision (MEDIUM)

The tag `N` from `st.counter` is bumped once per AwaitSuspend.
But multiple awaits in the same function will have
`aw.*.N`/`aw.*.M`/... all in the same function scope. Names
like `aw.st.ptr.N` must not collide with anything else. Use a
unique `aw.` prefix.

### R3 — Coroutine cleanup path drop-glue (MEDIUM — deferred)

If the outer coroutine is destroyed at a suspend point
(switch branch `i8 1`), control jumps to `coro.cleanup`.
Locals alive at that point would leak. This is a general
issue affecting v5.5.4 + v5.5.5 + v5.5.6 — not unique to
v5.5.5. Deferred to v5.5.7 sanitizer hardening.

### R4 — Fixed-point shift (LOW)

IR change only affects async-containing modules. `mnc_all.mn`
has no async, so stage2.ll delta will be tiny. Expect <0.1%.

### R5 — Goldens execute tests break (EXPECTED)

The 5 Sh.4 goldens will now **register_wait** but nothing
resumes them. They'll likely hang in `coro.suspend` forever
until the OS kills the process. This is expected — v5.5.6
wires the scheduler.

**Mitigation:** don't run the goldens' execute-test in v5.5.5.
Do run `llvm-as` + `opt -O1` + `llc` to confirm the IR is
structurally valid.

---

## What NOT to do

- Do not touch BlockOn in v5.5.5 — defer scheduler integration
  to v5.5.6.
- Do not modify the outer fn's epilogue (coro.final/cleanup/
  ret blocks emitted by v5.5.4) — they're the jump targets
  for the new switch.
- Do not inject `__mn_coro_scheduler_init` in main — v5.5.6.
- Do not add a new MIR variant — AwaitSuspend already exists.
- Do not skip the `opt -O1` step in the test scripts. llc
  alone crashes on coro intrinsics per v5.5.4 Q2 finding.
