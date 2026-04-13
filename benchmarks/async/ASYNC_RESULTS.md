# Async Benchmark Suite: v4.94.0 Baseline

**Date:** 2026-04-13
**Hardware:** WSL2 on Windows, AMD/Intel
**Method:** 5 runs per configuration, drop highest and lowest, report median

---

## Status

### Mapanare async benchmarks

**Compilation:** All 5 benchmarks compile through the full Python bootstrap
pipeline and pass `llvm-as` validation at O2. The emitted IR contains
real `coro.suspend` points, scheduler registration calls, and the
`__mn_coro_scheduler_init(i32 0)` auto-detect-cores initialization.

**Linking:** Currently fails because `libmapanare_rt.a` has not been
rebuilt with the v4.93.0 multi-threaded scheduler. The runtime source
(`mapanare_runtime.c`) contains the full implementation; a `make` in
`runtime/native/` will produce a linkable library. This is a build
infrastructure issue, not a correctness issue.

**Runtime measurements deferred** until the static library is rebuilt.
The benchmark harness (`run_async.py`) is ready and will produce JSON
with thread-count scaling when the link step succeeds.

### Python asyncio baseline (measured)

| Benchmark | Python (ms) | Tasks | Description |
|-----------|------------|-------|-------------|
| 01_sequential_chain | 82.5 | 100 | Linear await chain, no parallelism |
| 02_fanout | 81.5 | 100 | Independent tasks, max parallelism |
| 03_io_bound | 87.8 | 1000 | Minimal-work I/O simulation |
| 04_mixed_cpu_io | 83.7 | 50 | Alternating CPU + I/O tasks |
| 05_backpressure | 84.6 | 50 | 3-stage pipeline per iteration |

**Note:** Python asyncio is single-threaded (GIL). All benchmarks show
~82-88ms, dominated by Python interpreter startup + asyncio event loop
overhead. The actual task work is negligible. These numbers establish the
Python baseline for future comparison.

### Go goroutine baseline

**Not measured:** Go is not installed in this environment. Go programs
are written and ready to run. Install Go and run:
```bash
python benchmarks/async/run_async.py --cross-language
```

---

## Table 1: Benchmark Descriptions

| # | Name | Tasks | Pattern | What it measures |
|---|------|-------|---------|-----------------|
| 1 | sequential_chain | 100 | Linear await chain | Suspend/resume overhead (no parallelism) |
| 2 | fanout | 100 | Independent CPU tasks | Maximum parallelism, work-stealing efficiency |
| 3 | io_bound | 1000 | Minimal-work tasks | Task creation + scheduling overhead |
| 4 | mixed_cpu_io | 50 | Alternating CPU/IO | Heterogeneous workload handling |
| 5 | backpressure | 50x3 | 3-stage pipeline | Dependency chain, no free parallelism |

## Table 2: Expected Checksums

| Benchmark | Checksum | Verification |
|-----------|----------|-------------|
| 01_sequential_chain | 5050 | sum(1..100) |
| 02_fanout | 171700 | sum(i*(i+1)/2 for i in 1..100) |
| 03_io_bound | 1000 | 1000 tasks x 1 each |
| 04_mixed_cpu_io | 12000 | even: sum(1..i), odd: i, for i in 1..50 |
| 05_backpressure | 2500 | sum((i+1)*2-1 for i in 0..49) |

All checksums verified against Python asyncio equivalents.

---

## Table 3: Mapanare Thread-Count Scaling (PENDING)

*To be filled when libmapanare_rt.a is rebuilt with the v4.93.0 scheduler.*

| Benchmark | N=1 (ms) | N=2 (ms) | N=4 (ms) | N=auto (ms) | Scaling |
|-----------|----------|----------|----------|-------------|---------|
| 01_sequential_chain | — | — | — | — | — |
| 02_fanout | — | — | — | — | — |
| 03_io_bound | — | — | — | — | — |
| 04_mixed_cpu_io | — | — | — | — | — |
| 05_backpressure | — | — | — | — | — |

## Table 4: Cross-Language Comparison (PARTIAL)

| Benchmark | Mapanare (ms) | Go (ms) | Python (ms) | MN vs Go | MN vs Py |
|-----------|-------------|---------|------------|----------|----------|
| 01_sequential_chain | — | — | 82.5 | — | — |
| 02_fanout | — | — | 81.5 | — | — |
| 03_io_bound | — | — | 87.8 | — | — |
| 04_mixed_cpu_io | — | — | 83.7 | — | — |
| 05_backpressure | — | — | 84.6 | — | — |

---

## How to reproduce

```bash
# Rebuild the C runtime (required for linking)
cd runtime/native && cc -O2 -shared -fPIC -pthread mapanare_runtime.c -o libmapanare_runtime.so && cd ../..

# Run all benchmarks
python benchmarks/async/run_async.py --runs 5 --cross-language

# Run a single benchmark
python benchmarks/async/run_async.py --only 02_fanout --runs 10
```

## Data files

| File | Description |
|------|-------------|
| `v4.94.0-baseline.json` | Raw benchmark data (Python baselines + Mapanare compile status) |
| `run_async.py` | Benchmark harness (compile, run, measure, compare) |
| `*.mn` | Mapanare async benchmark programs (5) |
| `*.go` | Go goroutine equivalents (5) |
| `*.py` | Python asyncio equivalents (5) |
