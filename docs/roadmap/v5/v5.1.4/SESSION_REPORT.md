# v5.1.4 Session Report — Perf.2: Lazy Thread Creation

## Narrative

v4.150.0 (E6) discovered that the async benchmark's "0.85x Go" headline
required `MAPANARE_ASYNC_THREADS=2` — the default (auto-detect cores)
spent ~2.2 ms in `pthread_create` on a 32-core machine, dominating the
benchmark total. Mamba v4.154.0 (lines 174-180) called this out: the
headline is not a portable claim without the qualifier.

v5.1.4 eliminates the qualifier by replacing the eager thread pool with
lazy creation:

1. **Pre-create 2 workers** (worker 0 = caller, worker 1 = 1 spawned
   thread). This matches the `ASYNC_THREADS=2` configuration that
   produced the 0.85x number.
2. **Lazy spawn on queue pressure** — when `active_tasks > workers * 8`
   and `workers < worker_cap`, spawn one more thread under `spawn_lock`.
3. **Idle exit** — workers that haven't processed a task for 100 ms and
   `live_workers > 1` (keeping total >= 2) exit cleanly. The slot is
   reusable via `mn_find_worker_slot` (join-and-reclaim pattern).
4. **Race-safe teardown** — `__mn_coro_scheduler_destroy` joins only
   threads that were actually spawned (`spawned[i]` array). Workers
   that idle-exited have already terminated; `pthread_join` returns
   immediately for them.

## Changes made

1. `runtime/native/mapanare_runtime.c`:
   - **Struct** `mn_mt_scheduler_t`: renamed `num_workers` to
     `worker_cap`, added `live_workers` (atomic), `spawned[]`,
     `worker_exited[]` (atomic), `spawn_lock` mutex.
   - **`mn_worker_get_task`**: steal scan uses `worker_cap` instead
     of `num_workers`.
   - **`mn_worker_loop`**: added idle-exit logic — tracks
     `last_work_us` via `mapanare_time_us()`, exits after 100 ms idle
     when `live_workers > 1`, sets `worker_exited[id]`.
   - **New `mn_find_worker_slot`**: scans for reusable slots (exited
     threads are joined and reclaimed) or unused slots.
   - **New `mn_spawn_worker_locked`**: spawns a single worker thread
     at a free slot, under `spawn_lock`.
   - **`__mn_coro_scheduler_init`**: pre-creates only 1 thread
     (worker 1), not `cap-1`. `MAPANARE_ASYNC_THREADS` env var
     preserved as override.
   - **`__mn_coro_scheduler_register`**: adds lazy spawn check after
     task push — spawns another worker when tasks > workers * 8.
   - **`__mn_coro_scheduler_destroy`**: iterates `spawned[]` array
     instead of `1..num_workers`; destroys `spawn_lock`.

2. `docs/roadmap/v5/v5.1.4/`:
   - `HYPOTHESIS.md` — pre-edit hypothesis
   - `RESULTS.md` — scenario matrix + 5% rule PASS
   - `SESSION_REPORT.md` — this file

## Results

| Metric | Before | After | Status |
|---|---|---|---|
| Default async geomean | ~2.3 ms | 1.19 ms | **-48.4%** |
| Default vs Go | 1.7x | 0.91x | **PASS** |
| Tuned (ASYNC_THREADS=2) | ~1.14 ms | 1.15 ms | +0.9% (no regr.) |
| CPU geomean | 0.383 ms | 0.383 ms | No change |
| TSan races | 0 | 0 | Clean |
| Valgrind leaks | 0 | 0 | Clean |
| Golden tests | 54/66 | 54/66 | No change |

## Verification

- TSan: scheduler lifecycle test + 3 async golden programs, 0 races
- Valgrind memcheck: 0 errors, 0 leaks
- Valgrind helgrind: 3 false positives (GCC atomics, TSan confirms clean)
- Golden tests: 54/66 (byte-identical to v5.1.3)
- Async benchmarks: 10-run medians, all 5 correct checksums
- CPU benchmarks: 6 workloads, no regression
- `make build-rt`: compiles cleanly
- `python3 scripts/build_stage1.py`: links cleanly (3,648,672 bytes)

## Key insight

The implementation validates v4.150.0's analysis: the async runtime is
already faster than Go at actual dispatch. The entire 2.3 → 1.19 ms
improvement is pure startup overhead elimination (fewer `pthread_create`
calls). The `MAPANARE_ASYNC_THREADS` env var is preserved as an override
but no longer needed for the headline claim.
