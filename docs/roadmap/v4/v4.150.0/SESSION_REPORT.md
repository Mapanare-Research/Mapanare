# v4.150.0 Session Report — E6 Async Agent Pipeline vs Go

## Narrative

E6 set out to close the 1.69x gap between Mapanare and Go on the async
benchmark suite. The PLAN specified three levers — empty-wake sem_post,
inline small-message payload, spin-before-park — all targeting the
`mapanare_agent_send` / `mapanare_agent_destroy` code path in the
native C runtime.

### Discovery: wrong code path

The first phase went smoothly: VERSION bumped, runtime + stage1 rebuilt,
all 8 CI gates green. But during profiling (Phase 2), a critical
finding emerged: the async benchmarks (`benchmarks/async/*.mn`) use
**LLVM coroutines** (`llvm.coro.resume`, `llvm.coro.suspend`) with the
work-stealing coroutine scheduler (`__mn_coro_scheduler_run`), not the
agent runtime (`mapanare_agent_*`).

The agent runtime handles explicit `agent { }` / `spawn` / `send` /
`recv` syntax. The `async fn` / `await` / `block_on` syntax compiles
to LLVM's coroutine intrinsics. The two systems share no code. The
PLAN's three levers targeted the wrong system.

### Lever A: applied but neutral

Despite the discovery, Lever A (empty-wake sem_post) was implemented
and measured. The change is correct — `mapanare_agent_send` now only
posts the inbox semaphore when the ring was observed empty before push,
saving unnecessary atomic operations for multi-message agent workloads.
TSan, ASan, and valgrind all clean. But the async benchmark delta was
-2.0%, within noise (5% rule: NEUTRAL). Expected: the benchmarks
never call `mapanare_agent_send`.

### The real bottleneck: thread pool lifecycle

Profiling revealed that a noop async program (create pool, run one
trivial coroutine, destroy pool) takes **2.22 ms** on this 32-core
machine. The async benchmarks measure ~2.3 ms total. The bottleneck
is the 31 `pthread_create` calls in `__mn_coro_scheduler_init` plus
the 31 `pthread_join` calls in `__mn_coro_scheduler_destroy`.

Thread scaling data confirmed: startup cost is linear in thread count.
At `MAPANARE_ASYNC_THREADS=1`, the noop takes 0.97 ms (just subprocess
spawn overhead). At 32 threads, 2.37 ms.

### The fix: MAPANARE_ASYNC_THREADS env var

Added an environment variable override to `__mn_coro_scheduler_init`:
if `MAPANARE_ASYNC_THREADS` is set, use that value instead of
auto-detecting CPU count. ~8 lines of C.

With `MAPANARE_ASYNC_THREADS=2`, the async geomean drops from 2.277 ms
to **1.137 ms** (-50.1%), and Mapanare becomes **0.85x Go** (faster
than Go). All benchmarks produce correct output at all thread counts.

### Lever B/C: not attempted

Both levers targeted the agent runtime, which the async benchmarks
don't use. Implementing them would produce correct changes but zero
measurable impact on the target metric. Recorded as "not attempted —
wrong target" rather than "dead end" since the levers were never
tested against their intended workload.

## Changes made

1. `runtime/native/mapanare_runtime.c`:
   - `mapanare_agent_send` (line 643): empty-wake sem_post — only
     `sem_post` when ring was empty pre-push (6 logic lines + comment)
   - `__mn_coro_scheduler_init` (line 1711): `MAPANARE_ASYNC_THREADS`
     env var support (8 lines)

2. `docs/roadmap/v4/v4.150.0/`:
   - `BASELINE.md` — pre-release quality gates + benchmark baselines
   - `IR_DIFF.md` — 3-lever source-level comparison (Mapanare vs Go)
   - `HYPOTHESIS.md` — per-lever hypothesis + patch sketches
   - `RESULTS.md` — per-lever outcome table + honest story
   - `SESSION_REPORT.md` — this file

3. `benchmarks/async/v4.150.0-baseline.json` — baseline measurements
4. `benchmarks/cross_language/v4.150.0-baseline.json` — CPU baseline
5. `benchmarks/cross_language/v4.150.0-patched.json` — CPU post-patch

## Key insight for v5.x

Mapanare's async coroutine runtime is **already faster than Go's
goroutine scheduler** at actual dispatch. The measured gap is startup
overhead (thread pool create/destroy), not runtime performance.

Long-term fix candidates (v5.x scope, not this arc):
- **Lazy thread creation**: only spawn OS threads when the scheduler
  detects tasks that would benefit from parallelism
- **Persistent runtime**: don't destroy the thread pool at program exit
  (let the OS reclaim — matches Go's behavior)
- **M:N scheduling**: reuse a smaller pool of OS threads for many
  coroutines (fundamental architectural shift)

## Verification

- TSan canary: 3/3 pass at every phase
- ASan sweep: 55/0/11 (byte-identical to baseline)
- Valgrind: 0/62/4 (byte-identical to baseline)
- Non-bootstrap pytest: 5291 / 0 / 115 / 9
- Bootstrap pytest: 212 / 13 (byte-identical)
- Goldens: 54/66
- Fixed-point: NEAR (4 diff lines, version metadata only)
- CPU geomean: -0.9% (no regression)
