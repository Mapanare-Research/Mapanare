# v5.1.4 Hypothesis — Perf.2: Lazy Thread Creation

## Target

Async benchmark geomean at **default settings** (no `MAPANARE_ASYNC_THREADS`
env var) on a multi-core machine.

## Baseline

| Scenario | geomean (ms) | ratio vs Go |
|---|---|---|
| Default (auto-detect cores) | ~2.3 ms | ~1.7x Go |
| `MAPANARE_ASYNC_THREADS=2` | 1.14 ms | 0.85x Go |

Source: v4.150.0 E6 analysis on 32-core machine.

## Root cause

`__mn_coro_scheduler_init` creates one OS thread per CPU core eagerly.
On a 32-core machine, 31 `pthread_create` calls take ~2.2 ms, dominating
the ~2.3 ms benchmark total. The actual coroutine dispatch is already
faster than Go — the gap is pure thread-pool startup overhead.

v4.150.0 added the `MAPANARE_ASYNC_THREADS` env var as a workaround.
Setting it to 2 drops the geomean to 1.14 ms (0.85x Go). But Mamba
v4.154.0 correctly flagged this: the headline "0.85x Go" is not a
portable claim if it requires a tuning knob.

## Hypothesis

Pre-creating 2 workers eagerly (worker 0 = caller thread, worker 1 =
1 spawned thread) eliminates the startup tax. Additional workers are
spawned lazily when pending tasks exceed workers x 8, up to the cap.
Idle workers self-exit after 100 ms when the pool has > 2 workers.

This matches Go's runtime scheduler pattern at a high level: threads
are created lazily and exit when idle.

## Expected outcome

| Scenario | target geomean (ms) | target ratio vs Go |
|---|---|---|
| Default (no env var) | <= 1.2 ms | <= 1.0x Go |
| `ASYNC_THREADS=2` (preserved) | <= 1.14 ms | no regression |

## 5% rule

- Default geomean must improve by >= 5% to ship (2.3 ms -> <= 1.2 ms
  is ~48% improvement, well above threshold).
- Tuned case (`ASYNC_THREADS=2`) must not regress by > 2%.

## Non-target watch list

- No CPU benchmark should regress.
- CPU geomean delta within +/- 1% noise.

## GitNexus pre-flight

Impact analysis: **LOW risk**. `__mn_coro_scheduler_init`,
`mn_worker_loop`, and `__mn_coro_scheduler_destroy` are self-contained
runtime internals with 0 upstream callers in the knowledge graph.
Called only from emitted LLVM IR (`call void @__mn_coro_scheduler_init(i32 0)`).
No cross-module or cross-language dependencies.
