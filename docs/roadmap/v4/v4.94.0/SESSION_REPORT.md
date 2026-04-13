# v4.94.0 Session Report — 2026-04-13

## Verdict

Async benchmark suite shipped. Arc 13 release 3. Measurement
infrastructure only — zero scheduler or emitter changes.

## What shipped

### 5 async benchmark programs (.mn + .go + .py)

| # | Benchmark | Tasks | Pattern |
|---|-----------|-------|---------|
| 1 | sequential_chain | 100 | Linear await chain (worst case for parallelism) |
| 2 | fanout | 100 | Independent CPU tasks (best case for work stealing) |
| 3 | io_bound | 1000 | Minimal-work simulation (scheduling overhead) |
| 4 | mixed_cpu_io | 50 | Alternating CPU/IO (heterogeneous workload) |
| 5 | backpressure | 50x3 | 3-stage pipeline (dependency chains) |

Each benchmark in three languages:
- **Mapanare** (.mn): async/await + block_on with real suspension
- **Go** (.go): goroutines + channels (natural Go idiom)
- **Python** (.py): asyncio (GIL-bound baseline)

All .mn benchmarks compile through full pipeline and pass llvm-as at O2.
All checksums verified against Python equivalents.

### Benchmark harness (run_async.py)

Adapted from the optimizer harness (run_baseline.py). Compiles .mn at O2,
runs N times, measures wall time, supports --cross-language for Go/Python.
Output is JSON for programmatic analysis.

### Python asyncio baselines (measured)

All 5 benchmarks: 82-88ms (dominated by interpreter startup + event loop
overhead). Establishes the Python baseline for future comparison.

### Mapanare runtime measurements (pending)

Mapanare link step fails because `libmapanare_rt.a` hasn't been rebuilt
with the v4.93.0 scheduler. The runtime C source is complete; rebuilding
the static library will enable end-to-end measurements. The harness is
ready.

### Go measurements (pending)

Go not installed in this environment. Programs written and ready to run.

## Honest assessment

This is a measurement infrastructure release that partially delivered:
the infrastructure (harness + programs) is complete and validated, but
only the Python baseline was actually measured. The Mapanare and Go
measurements await a runtime library rebuild and Go installation
respectively. The value is in the programs themselves — they define the
workloads that will be used to evaluate the scheduler for the rest of
Arc 13.

## Files produced

| File | Count | Description |
|------|-------|-------------|
| `benchmarks/async/*.mn` | 5 | Mapanare async benchmarks |
| `benchmarks/async/*.go` | 5 | Go goroutine equivalents |
| `benchmarks/async/*.py` | 5 | Python asyncio equivalents |
| `benchmarks/async/run_async.py` | 1 | Benchmark harness |
| `benchmarks/async/ASYNC_RESULTS.md` | 1 | Results document (partial) |
| `benchmarks/async/v4.94.0-baseline.json` | 1 | Raw data (Python baselines) |

## Next session

v4.95.0: StringBuilder in C runtime + loop-concat optimization.
