# v4.92.0 Session Report — 2026-04-13

## Verdict

Real suspension at await points shipped. Arc 13 release 1.

- `await` in async functions now emits `coro.save + coro.suspend + switch`
  (real LLVM coroutine suspension) instead of an inline-resume loop.
- C runtime coroutine scheduler implemented (`__mn_coro_scheduler_*`).
- `block_on()` uses the scheduler to drive coroutines cooperatively.
- Async file I/O runtime function added (`__mn_file_read_async`).
- Golden test 58 validates multi-await real suspension.
- All 3 existing async tests (55/56/57) updated and pass llvm-as.
- 1408/1408 core tests pass (8 pre-existing failures only).

## What shipped

### Real suspension emission (emit_llvm_text.py)

`_do_await_suspend()` now checks `self._fn_is_async`:
- **Inside async fn:** emits fast-path readiness check, then drive inner
  coroutine once, then if still pending: register with scheduler via
  `__mn_coro_register_wait(handle, future)` + `coro.suspend`. The
  scheduler resumes the coroutine when the future becomes Ready.
- **Outside async fn (fallback):** retains inline-resume loop for safety.

### Scheduler-driven block_on (emit_llvm_text.py)

`_do_block_on()` now emits:
1. `__mn_coro_scheduler_register(handle)` — register coroutine
2. `__mn_coro_scheduler_run()` — drive all pending coroutines
3. Extract value, destroy frame, free future (unchanged)

### Scheduler init/destroy in main

When the module has async functions:
- Entry: `__mn_coro_scheduler_init(64)` at start of main's first block
- Exit: `__mn_coro_scheduler_destroy()` before `__mn_intern_destroy()`

### Async function return type fix

Async functions now correctly register `ptr` as their return type in
`_sigs` (instead of the declared return type). This ensures callers
load the Future handle as `ptr`, not `i64`.

### Ret rewriting in non-MIR blocks

The async function ret→future-store rewriting now also processes
emitter-generated blocks (await.ready, drop glue), not just MIR blocks.

### C runtime (mapanare_runtime.c)

- `mn_coro_scheduler_t` — dynamic array of registered coroutines
- `__mn_coro_scheduler_init/register/step/run/destroy` — full lifecycle
- `__mn_coro_register_wait` — associate coroutine with awaited future
- `__mn_file_read_async` — spawns thread, reads file, sets future Ready
- Scheduler step resumes coroutines whose awaited futures are Ready
- Done detection via LLVM switched-resume suspend index convention

### Test updates

- 6 async tests updated to match scheduler-driven model
- Golden test 58: multi-await with real suspension
- All tests pass llvm-as validation

## Files changed

| File | Change |
|------|--------|
| `mapanare/emit_llvm_text.py` | Real suspend in `_do_await_suspend`, scheduler block_on, main init/destroy, async sig fix, ret rewriting |
| `mapanare/types.py` | `block_on` and `__mn_file_read_async` added to builtins |
| `runtime/native/mapanare_runtime.c` | Coroutine scheduler + async file I/O |
| `runtime/native/mapanare_runtime.h` | Scheduler + async I/O declarations |
| `tests/golden/58_async_file_io.mn` | New golden test |
| `tests/llvm/test_block_on.py` | Updated for scheduler model |
| `tests/llvm/test_async_golden.py` | Updated block_on assertions |
| `tests/llvm/test_coroutine_lowering.py` | Updated GEP assertion |

## Next session

v4.93.0: multi-threaded work-stealing scheduler. With real suspension
proven on a single thread, coroutines can be distributed across N worker
threads.
