# Mapanare v5.5.6 — "Scheduler-driven BlockOn + main lifecycle"

> **Third real-coroutine release. Replaces v5.5.4's synchronous
> BlockOn emission with the real scheduler_register +
> scheduler_run pattern. Injects scheduler_init at main entry
> and scheduler_destroy at main exits. Combined with v5.5.5's
> scheduler-driven AwaitSuspend, this is the release where
> Sh.4 goldens execute correctly AGAIN (having hung in v5.5.5).
> First release with real multi-threaded concurrency.**

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.5.5 shipped (scheduler-driven AwaitSuspend)
**Estimated work:** 1 session (~2–3 hours)

---

## Why this release exists

### v5.5.5 leftover

v5.5.5 made outer coroutines properly suspend via
`coro.save`/`coro.suspend`/switch + `register_wait(coro.hdl,
future)`. The scheduler now KNOWS which coroutines are waiting
on which futures. But nothing calls `__mn_coro_scheduler_run`
— the scheduler never runs — so the awaiting coroutine is
never resumed.

v5.5.6 wires the drive loop.

### Two independent changes, one release

**Change A — `BlockOn` scheduler integration.** Instead of
inline `llvm.coro.resume`, call:

```
%bo.hdl.N = load handle                  ; BEFORE register
call void @__mn_coro_scheduler_register(ptr %bo.hdl.N)
call void @__mn_coro_scheduler_run()     ; drives ALL pending tasks
; future is now Ready (scheduler ran everything to completion)
%bo.val.box.N = load future.payload
%bo.val.N = load i64, %bo.val.box.N
%dest = add i64 0, %bo.val.N
call void @llvm.coro.destroy(ptr %bo.hdl.N)
call void @free(box)
call void @free(future)
```

`scheduler_run` is the magic — it participates as a worker
thread AND coordinates N other worker threads (lazy-spawned).
It drains active_tasks to 0 before returning. When it returns,
our future is guaranteed Ready.

**Change B — main() scheduler lifecycle.** The scheduler
must be initialized before any async fn runs and destroyed
after. Inject at main entry:

```
call void @__mn_coro_scheduler_init(i32 0)   ; 0 = auto CPU count
```

And before every main exit (both `ret i32 <val>` variants):

```
call void @__mn_coro_scheduler_destroy()
```

Both changes are gated on `_module_has_async` — set once per
module at `emit_mir_module` entry by scanning `module.functions`
for any `fn_is_async(f) == true`.

### Why Change A + Change B ship together

Change A's BlockOn emits `@__mn_coro_scheduler_register`,
which `runtime/native/mapanare_runtime.c:1910–1919` rejects
with an error message if the scheduler isn't initialized:

> "mapanare: async runtime: cannot spawn task — scheduler not
> initialised."

So Change A without Change B = every async golden exits with
that error. Ship together.

### What this release closes

After v5.5.6, the 5 Sh.4 goldens execute correctly **through
the full Python-parity async pipeline**: scheduler init →
async fn returns future (initial suspend) → BlockOn registers
with scheduler → scheduler_run drives worker threads →
workers call llvm.coro.resume on the registered handles →
body runs → final suspend → register_wait relationships
drained → BlockOn extracts → destroy → free → scheduler_destroy
joins threads.

This is the release that makes async Mapanare actually
concurrent.

---

## Scope

### What ships

#### 6.1 — Real `BlockOn` emission

`emit_llvm.mn::emit_mir_by_kind` (the `kind == "block_on"`
branch). Replace v5.5.4 synchronous pattern with:

```
; BlockOn(%dest, %future)
%bo.hdl.ptr.N = getelementptr inbounds {i8, ptr}, ptr %future, i32 0, i32 1
%bo.hdl.N     = load ptr, ptr %bo.hdl.ptr.N

; Register with scheduler + run
call void @__mn_coro_scheduler_register(ptr %bo.hdl.N)
call void @__mn_coro_scheduler_run()

; Extract value (v4.102.0 foot-gun: slot 1 is now the result box,
; NOT the handle anymore — reuse %bo.hdl.N from before register)
%bo.val.ptr.N = getelementptr inbounds {i8, ptr}, ptr %future, i32 0, i32 1
%bo.val.box.N = load ptr, ptr %bo.val.ptr.N
%bo.val.N     = load i64, ptr %bo.val.box.N
%dest         = add i64 0, %bo.val.N

; Cleanup
call void @llvm.coro.destroy(ptr %bo.hdl.N)
call void @free(ptr %bo.val.box.N)
call void @free(ptr %future)
```

**Expected LOC:** ~40 (delta from v5.5.4's ~25; only the
scheduler_register + scheduler_run lines are net-new).

#### 6.2 — Module-level `_module_has_async` flag

Add helper in `emit_llvm.mn`:

```
fn module_has_async(module: MIRModule) -> Bool {
    let mut i: Int = 0
    for _ in 0..5000 {
        if i >= len(module.functions) { return false }
        if fn_is_async(module.functions[i]) { return true }
        i = i + 1
    }
    return false
}
```

Compute once at `emit_mir_module` entry. Pass into
`emit_mir_function` via... the simplest route is a new
`EmitState` field:

```
module_has_async: Bool
```

This is the 23rd EmitState field — bumps struct registry. Reg.1
gate update required at lines 58, 126, 137, 182 of
`emit_llvm.mn`.

**Alternative:** make `module_has_async` a free helper and call
it inside `emit_mir_function` when f.name == "main". Avoids
EmitState bump but recomputes per main emission (there's only
one, so fine).

**Recommend alternative.** Saves Reg.1 bump. ~5 LOC helper +
inline call.

#### 6.3 — main() `__mn_coro_scheduler_init` / `_destroy` injection

In `emit_mir_function`, when `f.name == "main"`:

- After the `entry:` label emission but before the first
  instruction, emit `call void @__mn_coro_scheduler_init(i32 0)`
  IF `module_has_async(module)` is true.
- Each `ret i32 <val>` must be preceded by
  `call void @__mn_coro_scheduler_destroy()`.

Python does this at `emit_llvm_text.py:2499–2520` — has a
neat trick: it rewrites `ret i32 0` lines post-hoc after
emitting the whole body. Self-hosted can do the same or
intercept at `emit_mir_return` (when `current_ret_type ==
"i32"` and module has async, prepend destroy call).

**v5.5.6 decision:** intercept in `emit_mir_return`. Cleaner,
no line rewriting. Parallel to the ASYNC_PTR: pattern.

**LOC:** ~20 (module_has_async helper + init injection + destroy
interception in emit_mir_return).

### What does NOT ship

- **spawn + join builtins.** v5.5.8.
- **Multi-thread assertion goldens.** v5.5.8 can add
  `60_async_multi_fanout` that verifies `MAPANARE_ASYNC_THREADS`
  honored.
- **Valgrind/ASan/TSan sweep.** v5.5.7.
- **PARITY_GAPS.md update.** v5.5.9.

---

## Exit criteria

1. Stage1 rebuilds.
2. 5 Sh.4 goldens: compile, `llvm-as` clean, `opt -O1` clean,
   execute with **correct output** (42, 43, 110, done, 220).
3. `strace -e trace=clone,futex /tmp/59_async_fanout_v556.bin`
   shows `clone` calls (worker threads spawned). Evidence of
   real threading.
4. stage2.ll: llvm-as clean; self-hosting preserved.
5. Non-bootstrap pytest 0 failures.
6. `make lint` clean.
7. Goldens harness still 59/66 PASS.
8. Valgrind: no NEW errors on 55_async_basic (v5.5.6 may
   introduce leaks around scheduler init/destroy — acceptable
   to defer cleanup to v5.5.7 with explicit justification,
   but note must be in SESSION_REPORT).

---

## Design decisions

### D1 — `scheduler_init(0)` = auto CPU count

Passing 0 triggers `mapanare_cpu_count()` inside the runtime
(line 1860). Matches Python bootstrap emission at
`emit_llvm_text.py:2501`. Users can override via
`MAPANARE_ASYNC_THREADS` env var.

### D2 — Inject init via emit_mir_function, not emit_mir_module

The scheduler_init call must land INSIDE main's body (in the
entry block), not as module-level initialization. Main's
emit_mir_function path is the place to inject.

Python does this via line-rewriting (insert into first block's
lines post-emission). Self-hosted injects via emit_line at
the right moment — after entry label, before first
instruction.

### D3 — Destroy injection in emit_mir_return

When `current_ret_type == "i32"` (main) and module has
async, prepend scheduler_destroy. Parallel to v5.5.4's
ASYNC_PTR: pattern for async fns. Clean.

But wait — current_ret_type is only "i32" for main, and this
path also fires for non-async-using mains. We should ONLY
destroy when module_has_async. Need to thread that in.

**Options:**
- A. Add `module_has_async: Bool` to EmitState (+1 field, Reg.1
  bump).
- B. Sentinel `current_ret_type = "i32_async"` for
  "async-aware main". Emit_mir_function sets this when it
  emits main + module has async.

**Recommend B.** No struct registry bump, matches the
ASYNC_PTR: pattern. Specific sentinel string
"i32_ASYNC_MAIN" or just "i32_async".

### D4 — Future state after scheduler_run

After `__mn_coro_scheduler_run()` returns, all registered
tasks have drained. For the BlockOn-registered coroutine,
its final suspend has stored `i8 1` + box into the future.
Safe to extract.

What if the coroutine was destroyed before completion (e.g.,
an internal await failed)? For v5.5.6, goldens don't exercise
this. Document as a known gap; v5.5.7 + v5.5.8 harden.

### D5 — v4.102.0 foot-gun (handle reload)

Python comment at emit_llvm_text.py:5459:
> "after scheduler_run completes, that slot no longer holds
> the coroutine handle"

v5.5.4's BlockOn already handles this — loads handle ONCE
before scheduler_register (or in v5.5.4's case, before resume).
v5.5.6 preserves the pattern.

---

## Risks

### R1 — Deadlock on goldens (LOW)

The scheduler drains `active_tasks` to 0 before returning.
If the coroutine we registered never completes (e.g., awaits
something never set to Ready), scheduler_run would hang.
The 5 Sh.4 goldens all complete trivially (return const),
so no deadlock risk for them. Real-I/O-await tests would
stress this.

### R2 — Scheduler init/destroy ordering (MEDIUM)

Must be: init FIRST instruction of main, destroy BEFORE every
ret. If another instruction sneaks in (e.g., drop_glue emits
before scheduler_destroy), double-free or UAF possible.

Mitigation: scheduler_destroy is idempotent per v5.1.4 runtime
implementation. Drop glue fires BEFORE ret (already the
pattern). Scheduler_destroy after drop glue, before ret. OK.

### R3 — module_has_async false negative (LOW)

If the helper misses an async fn (e.g., fn_is_async bug),
scheduler_init never injected but BlockOn emits
scheduler_register → runtime error at runtime. Keep
fn_is_async's tests tight.

### R4 — Thread leak on abnormal exit (LOW — documented)

If main exits via abort() or assert failure before
scheduler_destroy, worker threads are leaked. Acceptable;
OS reclaims on process exit.

### R5 — Fixed-point shift (LOW)

`mnc_all.mn` has no async, so `module_has_async` returns false
and no injection happens. stage2.ll byte-identical (modulo
helper fn being in the IR). Delta <100 lines.

---

## What NOT to do

- Do not ship without Change A AND Change B together.
  Change A alone = runtime error.
- Do not call `scheduler_run` recursively. Python's BlockOn
  calls it once; multiple BlockOn in main would call it
  multiple times (fine — each drains to empty and returns).
- Do not try to initialize the scheduler in a module ctor
  (that's C++ practice, not Mapanare's). main-entry is the
  right place.
- Do not skip the `strace` verification in the release
  checklist — it's the gate that proves real threading
  happened vs. single-thread execution.
- Do not add `spawn`/`join` in this release. v5.5.8.
