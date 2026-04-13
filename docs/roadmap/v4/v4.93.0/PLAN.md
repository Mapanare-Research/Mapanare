# Mapanare v4.93.0 — Multi-Threaded Async Scheduler (Option B)

> **Arc 13 release 2.** v4.92.0 gave us real suspension — coroutines
> yield control at await points and the scheduler resumes them when
> their awaited future is ready. But the scheduler is still
> single-threaded: one event loop, one thread. v4.93.0 implements
> Option B from DESIGN.md section 8 (rejected at the time as v5.x
> scope): a multi-threaded work-stealing scheduler. N worker threads,
> each with a local task queue, stealing from peers when idle. Async
> workloads scale with core count.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.92.0
**Delta review:** No
**Full panel:** No (v4.96.0)
**Estimated work:** 1 sprint
**Theme:** Async scales to N cores. Work-stealing scheduler in the C runtime.

---

## Scope

The existing cooperative scheduler (`mapanare_coop_scheduler_t`) is a
circular ready queue on one thread. The coroutine scheduler
(`mapanare_coro_scheduler_t`) added in Arc 9 is also single-threaded.
Both work, but neither can exploit multiple CPU cores.

v4.93.0 adds `mapanare_scheduler_t` — a new top-level scheduler that
owns N pthreads (default = number of CPU cores), each running a local
task queue. When a coroutine is spawned via `spawn()`, it is enqueued on
the spawning thread's local queue. When a thread's queue empties, it
steals from a random peer. `block_on(future)` parks the calling thread
and wakes it when the future resolves.

The design follows Go's GMP model simplified for coroutines:
- **G** = coroutine handle (a suspended coroutine frame)
- **M** = OS thread (pthread)
- **P** = processor context (local run queue + scheduler state)

Each M has one P. P owns a local deque (work-stealing deque, Chase-Lev
algorithm). Global queue is the fallback for overflow and fairness.

### Key invariants

1. A coroutine handle is touched by at most one thread at a time.
2. `Future<T>` status transitions are atomic (relaxed store for Ready,
   acquire load for checking).
3. Worker threads park (futex/condvar) when all queues are empty — no
   busy-waiting.
4. `scheduler_destroy()` joins all threads and frees all resources.
5. Single-threaded mode (N=1) behaves identically to v4.92.0.

---

## Phase 1 — Scheduler design document

- [ ] Write `docs/roadmap/v4/v4.93.0/SCHEDULER.md`:
  - Work-stealing deque (Chase-Lev): push_bottom, pop_bottom, steal
  - Thread lifecycle: create, park, wake, join
  - Task states: Runnable, Suspended (waiting on future), Complete
  - Global overflow queue: tasks pushed when local deque is full
  - `spawn()` semantics: enqueue on current thread's local deque
  - `block_on()` semantics: park calling thread, scheduler runs, wake when future Ready
  - Memory ordering requirements: which operations need seq_cst, acq_rel, relaxed
  - Shutdown protocol: set `running = 0`, wake all parked threads, join

## Phase 2 — Implement `mapanare_scheduler_t` in C runtime

- [ ] Create `runtime/native/mapanare_scheduler.c` (new file):
  - `mapanare_scheduler_create(int n_threads)` — allocate scheduler, start N worker pthreads
  - `mapanare_scheduler_spawn(scheduler, coroutine_handle)` — enqueue a coroutine for execution
  - `mapanare_scheduler_block_on(scheduler, future_ptr)` — block calling thread until future is Ready
  - `mapanare_scheduler_destroy(scheduler)` — signal shutdown, join all threads, free resources
  - Chase-Lev work-stealing deque (lock-free, bounded, per-thread)
  - Global task queue (mutex-protected, unbounded, for overflow and rebalancing)
  - Worker loop: pop local -> steal from peer -> check global -> park
- [ ] Create `runtime/native/mapanare_scheduler.h` with the public API
- [ ] Add to build system (`Makefile` / CMakeLists)

## Phase 3 — Wire `spawn()` and `block_on()` builtins

- [ ] In `mapanare/emit_llvm_text.py`:
  - `spawn(async_fn_call)` emits: call the async fn (get coroutine handle), call `mapanare_scheduler_spawn(sched, handle)`
  - `block_on(future)` emits: call `mapanare_scheduler_block_on(sched, future_ptr)`
  - Add `@mapanare_global_scheduler` as a module-level global (initialized in `main()` prologue)
  - In `main()` prologue: emit `mapanare_scheduler_create(0)` (0 = auto-detect core count)
  - In `main()` epilogue: emit `mapanare_scheduler_destroy(sched)`
- [ ] Ensure single-threaded fallback: if `MAPANARE_SCHED_THREADS=1` env var, create scheduler with N=1

## Phase 4 — Fan-out benchmark

- [ ] Create `tests/golden/59_async_fanout.mn`:
  - Spawn N async tasks (e.g., 100 tasks that each compute fib(20))
  - Await all results, verify sum
  - Print wall time and task count
  - Verify concurrent execution: wall time with N threads < wall time with 1 thread (at least 2x speedup on >= 4 cores)
- [ ] Measure throughput scaling: run with MAPANARE_SCHED_THREADS=1,2,4,8 and record tasks/sec
- [ ] Create `tests/golden/59_async_fanout.expected`

## Phase 5 — Thread safety audit

- [ ] ThreadSanitizer (TSan) build of the C runtime + async test suite
- [ ] TSan clean on all async golden tests (55, 56, 58, 59)
- [ ] TSan clean on the fan-out benchmark at maximum thread count
- [ ] Stress test: 1000 tasks x 10 suspensions each, 8 threads, 100 repetitions. Zero races.
- [ ] Verify no use-after-free on coroutine frames across threads (ASan + TSan combined)

## Phase 6 — Backward compatibility + golden pass

- [ ] Single-threaded mode (N=1) produces identical output to v4.92.0 async tests
- [ ] Existing async golden tests pass unchanged (55, 56, 58)
- [ ] Full golden suite: 59/59 pass
- [ ] `make test` passes — no regressions
- [ ] `make lint` passes

## Phase 7 — LOW sweep + closeout

- [ ] Grep for `TODO(v4.93)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | `mapanare_scheduler_t` exists with create/spawn/block_on/destroy | `grep mapanare_scheduler_create runtime/native/mapanare_scheduler.c` |
| 2 | Work-stealing deque implemented (Chase-Lev) | Code review of deque operations |
| 3 | `spawn()` builtin wired to scheduler_spawn | IR inspection |
| 4 | `block_on()` builtin wired to scheduler_block_on | IR inspection |
| 5 | `59_async_fanout.mn` demonstrates multi-threaded execution | Wall time comparison: N threads vs 1 thread |
| 6 | Fan-out throughput scales with core count (at least 2x on 4 cores) | Benchmark output |
| 7 | TSan clean on all async tests | TSan log |
| 8 | Stress test: 1000 tasks x 10 suspensions x 8 threads x 100 reps, zero races | TSan log |
| 9 | Single-threaded mode (N=1) backward compatible | Golden test output matches v4.92.0 |
| 10 | Golden 59/59 pass | `python scripts/test_native.py` |
| 11 | `make test` + `make lint` pass | CI log |

---

## What this release does NOT do

- **Structured concurrency** — no nurseries, no task groups, no cancellation propagation. `spawn()` is fire-and-forget for now.
- **Async I/O integration with the scheduler** — the scheduler drives coroutines, but file/network I/O is still on separate threads (v4.92.0 model). Event-loop integration is future work.
- **Prioritized scheduling** — all tasks have equal priority. No priority queues.
- **Self-hosted emitter changes** — `emit_llvm.mn` is not updated.
- **Mobile scheduler** — mobile targets keep the cooperative single-threaded scheduler. The work-stealing scheduler is desktop/server only.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Data races in the work-stealing deque | medium | critical | Chase-Lev is a well-studied algorithm. Use the established memory orderings. TSan CI gate. |
| Worker threads busy-wait and waste CPU | medium | medium | Park threads using futex (Linux) or condvar (portable) when all queues empty. Verify CPU usage is near-zero when idle. |
| Coroutine frame accessed by two threads simultaneously | low | critical | Invariant: a coroutine handle is owned by exactly one thread. The deque transfers ownership atomically. TSan enforces. |
| Shutdown races (destroy while tasks still running) | medium | high | Scheduler destroy sets `running = 0`, wakes all threads, waits for drain, then joins. Test with tasks in-flight at shutdown. |
| Performance regression on single-threaded workloads | low | medium | Benchmark single-threaded (N=1) against v4.92.0. Scheduler overhead should be < 1us per spawn/resume. |

---

## After v4.93.0

v4.94.0 builds the async-specific benchmark suite: 5 workloads measuring throughput, latency, and CPU utilization, compared against Go goroutines. The scheduler from v4.93.0 gets its first real measurement.
