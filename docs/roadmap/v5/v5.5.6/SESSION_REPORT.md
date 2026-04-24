# v5.5.6 — Scheduler-driven BlockOn + main lifecycle

> **Third real-coroutine release. Replaces v5.5.4's synchronous
> `llvm.coro.resume` drive inside `BlockOn` with the real
> `__mn_coro_scheduler_register` + `__mn_coro_scheduler_run`
> pattern. Injects `__mn_coro_scheduler_init(0)` at main entry
> and `__mn_coro_scheduler_destroy()` before every main exit,
> gated on `module_has_async`. Combined with v5.5.5's
> scheduler-driven AwaitSuspend, all 5 Sh.4 goldens execute
> through the full Python-parity async pipeline. First release
> with real multi-threaded concurrency.**

**Status:** SHIPPED
**Breaking:** No (language surface unchanged)
**Goldens:** 59/66 unchanged; all 5 Sh.4 goldens execute
correctly (42, 43, 110, done, 220)

---

## What shipped

### 6.1 — `module_has_async` helper (`emit_llvm.mn`)

Free helper added near the `emit_mir_function` definition;
avoids bumping the EmitState struct registry (Reg.1 gate stays
at 22 fields).

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

`fn_is_async` is re-exported from `mir.mn` (already pub since
v5.5.1). Scan bound matches the fn-count budget used elsewhere
in the emitter.

### 6.2 — `emit_mir_function` signature change

Added `module: MIRModule` as a third parameter so the helper
can run inside the per-function emission path. One call site
updated in `emit_mir_module` (line ~4745):

```
- st = emit_mir_function(st, f_emit)
+ st = emit_mir_function(st, f_emit, module)
```

### 6.3 — `i32_async` sentinel for async-aware main

Parallel to v5.5.4's `ASYNC_PTR:` pattern. A new local
`main_module_has_async` is set once per function emission; main
with async gets `current_ret_type = "i32_async"`, main without
async stays `"i32"`, non-main async stays `"ASYNC_PTR:" + T`,
plain non-main fns stay `T`.

### 6.4 — `scheduler_init` injection in main's entry block

Emitted as the first buffered body line after
`s.in_entry_block = true`. The entry block's body buffer
flushes after the prelude (tracking-slot allocas + zero-inits)
and before any user instruction, so ordering is:
`alloca %str_track.N` → `store zeroinitializer` → `call void
@__mn_coro_scheduler_init(i32 0)` → first async call / first
BlockOn. `0 = auto-detect cores` (respects
`MAPANARE_ASYNC_THREADS` inside the runtime).

### 6.5 — `scheduler_destroy` in `emit_mir_return`

New `"i32_async"` branch mirrors the existing `"i32"` branch
but prepends
`call void @__mn_coro_scheduler_destroy()` between drop-glue
and the trunc + ret. Both the `Some(val)` and
`None`/fallback paths of `emit_mir_return` get the new branch.
Drop-glue fires first (already the pattern); destroy is
idempotent per v5.1.4 runtime.

### 6.6 — Real `BlockOn` emission (`emit_mir_by_kind`)

Replaces v5.5.4's synchronous pattern. Per-tag SSA names stay
`%bo.*.N`:

```
; v5.5.6 block_on <N> — scheduler-driven
%bo.hdl.ptr.N = getelementptr inbounds {i8, ptr}, ptr %future, i32 0, i32 1
%bo.hdl.N     = load ptr, ptr %bo.hdl.ptr.N
call void @__mn_coro_scheduler_register(ptr %bo.hdl.N)
call void @__mn_coro_scheduler_run()
%bo.val.ptr.N = getelementptr inbounds {i8, ptr}, ptr %future, i32 0, i32 1
%bo.val.box.N = load ptr, ptr %bo.val.ptr.N
%bo.val.N     = load i64, ptr %bo.val.box.N
%dest         = add i64 0, %bo.val.N
call void @llvm.coro.destroy(ptr %bo.hdl.N)
call void @free(ptr %bo.val.box.N)
call void @free(ptr %future)
```

v4.102.0 foot-gun preserved: `%bo.hdl.N` is loaded BEFORE
`scheduler_register` and reused after `scheduler_run` because
the scheduler overwrites `future.payload` (slot 1 of the
`{i8, ptr}` Future) with the result box, so re-reading slot 1
afterwards would hand `coro.destroy` an 8-byte malloc'd int
and segfault at `destroy_fn`.

---

## Verification

### 5 Sh.4 goldens — full pipeline

| Golden        | llvm-as | opt -O1 | output |
|---------------|---------|---------|--------|
| 55_async_basic     | ✓ | ✓ | **42**   |
| 56_async_await     | ✓ | ✓ | **43**   |
| 57_real_await      | ✓ | ✓ | **110**  |
| 58_async_file_io   | ✓ | ✓ | **done** |
| 59_async_fanout    | ✓ | ✓ | **220**  |

All 5 execute through the full Python-parity pipeline:
`scheduler_init` → `compute()` returns future (initial suspend)
→ `scheduler_register` → `scheduler_run` drives worker 0
(main) + pre-spawned worker 1 → inner body resumes → final
suspend → payload extracted → `coro.destroy` → `free` →
`scheduler_destroy`.

### Threading proof (59_async_fanout)

`strace -f -e trace=clone,clone3` with
`MAPANARE_ASYNC_THREADS=N`:

| N | clone count | note |
|---|---|---|
| 1 | 0 | cap=1 → prime=0, caller-only |
| 2 | 1 | cap=2 → prime=1 pre-spawn |
| 3 | 1 | cap=3 → prime=1 pre-spawn, no lazy |
| 4 | 1 | cap=4 → prime=1 pre-spawn, no lazy |
| 8 | 1 | cap=8 → prime=1 pre-spawn, no lazy |

v5.1.4 lazy-spawn gate (`tasks > workers*8`) doesn't trigger
on 59's 10 fast awaits; pre-spawned worker 1 plus caller (as
worker 0) handles the load. The PLAN.md §Phase 4.1 expectation
of `clone ≥ 3` was written assuming eager spawning — the
v5.1.4 policy is correct to stay lazy under small loads.

**Evidence that threading is real:** the `cap ≥ 2` cases each
show 1 clone3 (worker 1 pre-spawned via
`mapanare_thread_create` in `__mn_coro_scheduler_init`) and 1
futex sync between worker 0 (caller) and worker 1. With
`cap = 1` we get 0 clones as expected (main is the only
worker). Scaling up past cap=4 would require a goldens-level
workload that sustains queue pressure — v5.5.8's
`60_async_multi_fanout` is the right place.

### Self-hosting

| Metric | v5.5.5 | v5.5.6 | Delta |
|---|---:|---:|---:|
| stage2.ll lines | 194,553 | 194,799 | +246 (+0.13%) |
| stage2.ll `define` count | 906 | 907 | +1 (new helper) |
| stage2.ll `llvm-as` | OK | OK | — |

The +1 define is `module_has_async`. `mnc_all.mn` contains no
`async` decorators, so the helper returns `false` inside the
self-hosted compiler's own main, and no scheduler hooks are
emitted into stage2 — stage2 is still a plain synchronous
compiler driver.

### Tests

- **Goldens harness:** 59/66 PASS (unchanged vs v5.5.5).
- **Non-bootstrap pytest:** 5508 passed, 116 skipped, 9
  xfailed. One pre-existing test (`test_user_agent_contains_
  current_version`) failed at first run because the runtime
  archive had been compiled with `MAPANARE_VERSION=5.5.5`;
  `make build-rt` regenerated `libmapanare_rt.a` with the
  5.5.6 macro and the test passes. Same pattern as v5.5.5.
- **Bootstrap pytest:** 225 passed, 5 xfailed — unchanged.
- **`make lint`:** clean (ruff + black + mypy).

### Valgrind

`valgrind --error-exitcode=1 --errors-for-leak-kinds=definite
/tmp/55_async_basic_v556.bin` reports **0 errors** and **0
leaks**: 5 allocs / 5 frees (`coro.mem`, `future`, payload
box, two string-printer intermediates). This is a STRICT
improvement over v5.5.4: that release did `coro.resume` +
payload extract without ever calling `coro.destroy` or
`free(future)` — leaks were tolerated there. v5.5.6's real
BlockOn cleanup path closes them.

---

## Risk register — updated

| Risk | State | Note |
|---|---|---|
| R1 — Deadlock on goldens | NOT OBSERVED | all 5 goldens return via scheduler_run; fast-path + drain-to-zero pattern holds |
| R2 — Scheduler init/destroy ordering | LOW-realized | init emitted after prelude allocas, before first async call; destroy emitted after drop-glue, before trunc + ret |
| R3 — module_has_async false negative | NOT OBSERVED | fn_is_async correctness carried forward from v5.5.1 — no new code |
| R4 — Thread leak on abnormal exit | LOW-documented | scheduler_destroy injected only on structured exits (`ret` paths); `exit()`/`abort()` paths don't run it, OS reclaims |
| R5 — Fixed-point shift | LOW-realized | stage2.ll +0.13% (under <1% budget) |

---

## What did NOT ship (v5.5.7+ scope)

- **Sanitizer sweep.** TSan/ASan on 5 Sh.4 goldens.
  Current v5.5.6 output is valgrind-clean but TSan may flag
  scheduler internals (worker participation + mutex/cond
  patterns are v5.1.4 territory). v5.5.7.
- **Fixed-point recheck.** v5.5.4 regressed Ve.1 (mnc-stage2
  segfault during stage3 lex of mnc_all.mn). v5.5.6 inherits
  that state. v5.5.7 investigates.
- **Destroy-path drop-glue.** `coro.cleanup` currently frees
  only the coroutine frame; any leaked String / List /
  boxed resources captured in the coroutine frame are not
  dropped when a coroutine is destroyed before reaching
  final-suspend. No Sh.4 golden exercises this. v5.5.7.
- **Multi-thread assertion golden.** v5.5.8 can add
  `60_async_multi_fanout` (queue-pressure workload that
  forces lazy-spawn) to provide a stronger threading gate
  than strace on fast-completing goldens.
- **spawn + join builtins.** v5.5.8.

---

## Files changed

| File | Change |
|---|---|
| `VERSION` | 5.5.5 → 5.5.6 |
| `mapanare/self/emit_llvm.mn` | +60 / −15 (module_has_async helper + emit_mir_function param + i32_async sentinel + scheduler_init/destroy injection + real BlockOn) |
| `mapanare/self/mnc_all.mn` | regenerated |
| `mapanare/self/mnc-stage1` | rebuilt |
| `runtime/native/libmapanare_rt.a` | rebuilt (VERSION macro bump) |
| `docs/roadmap/v5/v5.5.6/SESSION_REPORT.md` | new |
| `CLAUDE.md` | v5.5.6 entry prepended |

---

## Commit narrative

1. `ee7b699` — v5.5.6: VERSION bump, baseline preserved
2. (next) — v5.5.6: scheduler-driven BlockOn + main lifecycle

---

## Handoff to v5.5.7

1. **TSan sweep** of the 5 Sh.4 goldens — scheduler
   concurrent write/read patterns (active_tasks,
   live_workers, per-worker deques, overflow queue) are all
   `__atomic_*` in v5.1.4 but the coroutine payload writes
   from `emit_mir_return` are plain stores. Any race there
   would need a relaxed-atomic or `memory_order_release`
   barrier.
2. **Ve.1 investigation** — v5.4.4 regressed mnc-stage2:
   segfault before stage3 emission. stage2.ll remains
   `llvm-as` clean (since v5.4.4 through v5.5.6) but
   execution of stage2 itself does not produce stage3.ll.
   Root cause still unknown.
3. **Drop-glue on `coro.cleanup`** — the current epilogue
   frees `coro.mem` but doesn't drop ownership of captured
   resources. Closes a leak class that v5.5.8's longer-lived
   coroutine goldens will expose.
