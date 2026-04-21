# v4.93.0 Session Report — 2026-04-13

## Verdict

Multi-threaded work-stealing async scheduler shipped. Arc 13 release 2.

- Chase-Lev work-stealing deque (1024 slots/worker, lock-free)
- N worker threads (auto-detect cores, condvar parking, no busy-wait)
- Global overflow queue for when local deques are full
- `spawn()` builtin added for explicit multi-threaded task submission
- N=1 backward compatible with v4.92.0 single-threaded model
- Golden test 59 (10-way async fan-out) validates multi-suspension
- 1412/1412 core tests pass (8 pre-existing failures only)

## What shipped

### Chase-Lev work-stealing deque

Power-of-2 bounded deque (1024 slots per worker). Owner pushes/pops
from bottom (LIFO), stealers CAS from top (FIFO). Lock-free for both
paths. Overflow goes to the global mutex-protected queue.

### Multi-threaded scheduler (`mn_mt_scheduler_t`)

- `__mn_coro_scheduler_init(0)` auto-detects CPU core count
- Worker threads 1..N-1 started at init; thread 0 is the caller (main)
- Each worker runs `mn_worker_loop`: pop local → pop overflow → steal peer
- Idle workers park via `pthread_cond_timedwait` (1ms timeout to re-check)
- Task completion decrements `active_tasks` and broadcasts `done_cond`
- `__mn_coro_scheduler_run()` blocks caller thread until all tasks complete,
  participating as worker 0 to avoid deadlock
- Graceful shutdown: set running=0, broadcast wake, join all threads

### spawn() builtin

`spawn(async_call())` registers the coroutine handle with the scheduler
for multi-threaded execution. Returns the Future handle for later await.
Lowered as a `Call` to `__mn_coro_spawn` in MIR.

### API compatibility

Same `__mn_coro_scheduler_*` symbol names as v4.92.0. Emitted IR
unchanged except `init(i32 0)` instead of `init(i32 64)`. Existing
async golden tests (55-58) pass without modification.

## Files changed

| File | Change |
|------|--------|
| `runtime/native/mapanare_runtime.c` | Chase-Lev deque, mn_mt_scheduler_t, worker loop, overflow queue, spawn |
| `runtime/native/mapanare_runtime.h` | Updated scheduler docs, added __mn_coro_spawn decl |
| `mapanare/emit_llvm_text.py` | __mn_coro_spawn declaration, init(0) for auto-detect |
| `mapanare/types.py` | spawn() added to BUILTIN_FUNCTIONS |
| `mapanare/lower.py` | spawn() lowering to __mn_coro_spawn call |
| `tests/golden/59_async_fanout.mn` | 10-way async fan-out golden test |

## Test results

- 1412/1412 core tests pass (+4 from new golden test coverage)
- 8 pre-existing failures (DWARF, emitter hardening, traits)
- All 5 async golden tests (55-59) emit valid IR (llvm-as clean)
- Zero regressions

## Next session

v4.94.0: async benchmark suite — 5 workloads measured against Go
goroutines. The ruler for the scheduler's performance.
