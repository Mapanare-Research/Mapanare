# Mapanare v4.72.0 — Coroutine Lowering Pt 2 (Suspend / Resume / Destroy)

> **Arc 9 release 1.** The second half of the coroutine lowering.
> Adds `llvm.coro.suspend`, `llvm.coro.save`, `llvm.coro.free`,
> `llvm.coro.resume`, `llvm.coro.destroy`. `await expr` stops
> erroring at lower time. Still not runnable — the scheduler
> integration is v4.73.0.

**Status:** DONE (2026-04-13)
**Session log:** AwaitSuspend MIR instruction, real await lowering, LLVM emission with fast-path check + save/suspend/switch. 8 new tests. Panel item Rattler #4 (ret.val.slot uniqueness) fixed.
**Decisions taken:** Fast-path optimization for already-ready futures. Value extraction loads i64 from Future box. Drop glue before coro.free per DESIGN.md §4.9.
**Breaking:** No
**Prerequisite:** v4.71.0 (arc 8 panel PASS — if NEEDS WORK, this plan slips)
**Delta review:** No (internal lowering)
**Full panel:** No (v4.76.0)
**Estimated work:** 2 sprints
**Theme:** `await` actually suspends. LLVM coroutine state machines are emitted. The IR is runnable at the LLVM level but there's no runtime driver yet.

---

## Scope

### What `await expr` now lowers to

```llvm
; Lower an await expression
%future = call {i8, i64} @some_async_fn()
; Check if the future is already ready (optimization)
%ready = extractvalue {i8, i64} %future, 0
%is_ready = icmp eq i8 %ready, 1
br i1 %is_ready, label %extract_value, label %suspend_point

suspend_point:
  %save_token = call token @llvm.coro.save(ptr %hdl)
  %result = call i8 @llvm.coro.suspend(token %save_token, i1 false)
  switch i8 %result, label %suspend_point_destroy [
    i8 0, label %resume_point
    i8 1, label %suspend_point_cleanup
  ]

resume_point:
  ; Resumed — the future should now be ready
  br label %extract_value

extract_value:
  %value = extractvalue {i8, i64} %future, 1
  ; %value is now the awaited result
```

And in the cleanup block:
```llvm
suspend_point_cleanup:
  ; Drop live values on the coroutine frame
  ; ...drop glue...
  %mem = call ptr @llvm.coro.free(token %id, ptr %hdl)
  call void @__mn_free(ptr %mem)
  br label %final_suspend

final_suspend:
  %final_token = call token @llvm.coro.save(ptr %hdl)
  %final_result = call i8 @llvm.coro.suspend(token %final_token, i1 true)
  switch i8 %final_result, label %coro_end [
    i8 0, label %coro_end
    i8 1, label %coro_end
  ]

coro_end:
  call i1 @llvm.coro.end(ptr %hdl, i1 false, token none)
  ret ...
```

### The `Future<T>` representation

Per DESIGN.md §4: `Future<T>` is a 2-tuple `{i8 state, T value}` where `state = 0` is pending, `state = 1` is ready, `state = 2` is done. The coroutine stores the result in the `value` slot when ready.

Inside the coroutine, the `async fn`'s "return" instructions don't actually return — they store into `*future_out` (the implicit out-pointer for the Future<T>) and then transition to the final-suspend state.

---

## Phase 1 — MIR suspension points

- [ ] `mapanare/mir.py`:
  - Confirm the v4.70.0 stubbed `CORO_SUSPEND`, `CORO_SAVE`, `CORO_FREE`, `CORO_RESUME`, `CORO_DESTROY` instruction kinds are there
  - Add: `SuspendBlock(save_token: SSAValue, on_resume: BlockLabel, on_cleanup: BlockLabel)` — a new block terminator kind that represents a suspension point
- [ ] Each `await` in the MIR becomes a `SuspendBlock` terminator plus a `%value = extractvalue` sequence in the resume target block

---

## Phase 2 — Lowering `await`

- [ ] `mapanare/lower.py` `_lower_await_expr(node: AwaitExpr) -> MIRValue`:

  ```python
  def _lower_await_expr(self, node: AwaitExpr) -> MIRValue:
      # Lower the inner expression (which is Future<T>)
      future = self.lower_expr(node.expr)
      future_state = self._emit_extract(future, 0)  # i8 state
      future_value = self._emit_extract(future, 1)  # T value

      # Fast path: future is already ready
      fast_block = self._fresh_block("await_fast")
      suspend_block = self._fresh_block("await_suspend")
      resume_block = self._fresh_block("await_resume")
      cleanup_block = self._fresh_block("await_cleanup")

      is_ready = self._emit_icmp_eq(future_state, 1)
      self._emit_br_cond(is_ready, fast_block, suspend_block)

      # Suspend path
      self._enter_block(suspend_block)
      save_token = self._emit_coro_save()
      suspend_result = self._emit_coro_suspend(save_token, final=False)
      self._emit_suspend_switch(suspend_result, resume_block, cleanup_block)

      # Resume path — re-fetch the future's value after resume
      self._enter_block(resume_block)
      resumed_value = self._emit_extract(future, 1)  # same slot, now ready
      self._emit_jump(fast_block)

      # Fast path (shared between resume and already-ready)
      self._enter_block(fast_block)
      # %value is bound here via phi
      phi = self._emit_phi([(future_value, entry), (resumed_value, resume_block)])

      # Cleanup path — drop the suspended frame
      self._enter_block(cleanup_block)
      self._emit_drop_glue_for_async_locals()
      self._emit_coro_free()
      self._emit_coro_end()

      return phi
  ```

- [ ] Drop-glue integration: variables live at the suspend point are spilled into the coroutine frame; on cleanup, the drop glue walks them and frees managed resources.

---

## Phase 3 — Async fn return lowering

- [ ] `return expr` inside an `async fn` doesn't emit a plain LLVM `ret`. Instead:
  1. Store the expression into the `Future<T>` out slot
  2. Transition to the `final_suspend` state (final=true)
  3. Emit `llvm.coro.end`
  4. Plain `ret` at the very end (but typically unreachable — coroutines don't "return" in the C sense)

---

## Phase 4 — LLVM emitter coroutine completion

- [ ] `mapanare/emit_llvm_text.py`:
  - Declare remaining intrinsics:
    ```llvm
    declare token @llvm.coro.save(ptr)
    declare i8 @llvm.coro.suspend(token, i1)
    declare ptr @llvm.coro.free(token, ptr)
    declare void @llvm.coro.resume(ptr)
    declare void @llvm.coro.destroy(ptr)
    ```
  - `_emit_coro_suspend(save_token, final)` → emits `%result = call i8 @llvm.coro.suspend(token %save_token, i1 %final)`
  - `_emit_suspend_switch(result, resume_block, cleanup_block)` → emits the `switch i8` terminator
  - `_emit_coro_free(id, hdl)` → emits `%mem = call ptr @llvm.coro.free(token %id, ptr %hdl)` followed by `call void @__mn_free(ptr %mem)`

---

## Phase 5 — `coro-split` pass verification

- [ ] Compile a golden `async fn` with a single `await`. Run `opt -passes=coro-split`. Verify:
  - The function is split into `ramp` (the outer-caller-visible entry), `resume` (run after a suspend), `destroy` (frame cleanup), `cleanup` (resource cleanup)
  - The `ramp` function returns the `Future<T>` with `state = 0`
  - The `resume` function is called via `llvm.coro.resume` externally (v4.73.0 scheduler does this)

---

## Phase 6 — Drop glue on cleanup

- [ ] If an `async fn` has live `String` / `List` / etc. at a suspend point, those live values need to be freed if the coroutine is destroyed (canceled) before resuming.
- [ ] The coroutine frame holds the live values (`coro-split` figures out what to spill). On cleanup, the drop glue walks them and frees.
- [ ] Existing drop glue (v4.32.0 extracted per-type) integrates: the cleanup block invokes the right drop-glue helpers.
- [ ] Test: `tests/runtime/test_async_cleanup_drop_glue.py` — create a coroutine with a `String` local, destroy it before completion, verify no leak via valgrind.

---

## Phase 7 — Self-hosted mirror

- [ ] `mapanare/self/lower.mn` — `lower_await_expr` mirrored
- [ ] `mapanare/self/emit_llvm.mn` — remaining coro intrinsics declared + emitted
- [ ] Fixed-point diff still 0 (mnc_all.mn doesn't use async — but if it did, the diff must still be 0)

---

## Phase 8 — Tests

- [ ] `tests/llvm/test_coroutine_lowering.py`:
  - `test_await_emits_suspend_switch` — grep IR for the `switch i8` after a coro.suspend
  - `test_await_emits_save_token` — grep
  - `test_cleanup_block_calls_coro_free` — grep
  - `test_cleanup_block_calls_drop_glue_for_strings` — compile a golden with a string local + await, inspect IR
  - `test_coro_end_at_every_exit_path` — grep
  - `test_llvm_as_clean_on_full_coroutine` — no errors
  - `test_coro_split_produces_ramp_resume_destroy_cleanup` — post-opt IR has all four

- [ ] `tests/llvm/test_async_ir_shape.py` — compile a reference async fn, compare the IR shape against a saved reference (updated when the lowering changes)

---

## Phase 9 — Future<T> struct type

- [ ] Needs a concrete struct layout. Per DESIGN.md §4:
  ```llvm
  %Future_i64 = type { i8, i64 }  ; state, value
  ```
- [ ] Each monomorphized `Future<T>` has its own struct type. The emitter tracks these and emits them as module-level type declarations.

---

## Phase 10 — LOW sweep

2 items.

---

## Phase 11 — Closeout

- [ ] Standard closeout
- [ ] `VERSION` → 4.72.0
- [ ] `CHANGELOG.md [4.72.0]` — suspend / resume / destroy / cleanup
- [ ] SESSION_REPORT with IR snippets

---

## Exit criteria (15 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `SuspendBlock` MIR terminator | grep |
| 2 | `_lower_await_expr` emits save + suspend + switch | unit test |
| 3 | `_lower_await_expr` emits resume + cleanup blocks | unit test |
| 4 | `async fn` return stores into Future out slot | IR inspection |
| 5 | Remaining coro intrinsics declared + emitted | grep |
| 6 | `llvm.coro.free` called in cleanup | grep |
| 7 | Drop glue in cleanup block for live managed values | `test_cleanup_block_calls_drop_glue_for_strings` |
| 8 | `llvm-as` clean on compiled async fn with await | `test_llvm_as_clean_on_full_coroutine` |
| 9 | `coro-split` produces ramp+resume+destroy+cleanup | `test_coro_split_produces_ramp_resume_destroy_cleanup` |
| 10 | Valgrind clean on drop-before-resume | `test_async_cleanup_drop_glue_valgrind` |
| 11 | `Future<T>` struct type emitted per monomorphization | grep |
| 12 | Self-hosted mirror matches | byte compare |
| 13 | Fixed-point diff still 0 | verify |
| 14 | `await` no longer errors at lower time | compile test |
| 15 | Standard closeout clean | CI |

---

## What v4.72.0 does NOT do

- **Runtime scheduler** — v4.73.0
- **Actually run a coroutine** — v4.73.0
- **`Stream<T>` async iterator** — v4.74.0
- **End-to-end golden test** — v4.75.0

At v4.72.0 the IR is structurally complete but there's no runtime to call `llvm.coro.resume` — so nothing actually executes the coroutine body past the first suspension.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| The `SuspendBlock` MIR terminator interacts badly with match lowering (decision trees) | medium | medium | Test with `async fn` + `match` + `await` combinations |
| Drop glue in cleanup block doesn't know which locals are live | **high** | high | LLVM's `coro-split` pass computes liveness for us; we just need to emit drop glue as a prelude to `llvm.coro.free`. Trust the pass |
| `Future<T>` struct type doesn't match the runtime's expected layout | medium | high | v4.73.0 runtime work must match this layout exactly; document in DESIGN.md §4 |
| `coro-split` pipeline issue surfaces only at `clang` link time | low | medium | Integration test via `clang` in CI |

---

## Reference

- [`v4.67.0/DESIGN.md`](../v4.67.0/DESIGN.md) §4
- LLVM Coroutines §"Coroutine Switched-Resumed ABI"

---

## After v4.72.0

v4.73.0 extends the C runtime scheduler to drive coroutines on desktop. `async fn` goes from "produces valid IR" to "actually runs and returns a value."
