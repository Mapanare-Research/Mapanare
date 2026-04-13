# Mapanare v4.94.0 — Async Benchmark Suite

> **Arc 13 release 3.** v4.92.0 shipped real suspension and v4.93.0
> shipped the multi-threaded scheduler. Before optimizing either, we
> need rigorous measurement. v4.94.0 builds 5 async-specific
> benchmarks, a measurement harness, and a cross-language comparison
> against Go goroutines. Pure measurement — zero scheduler or emitter
> changes. This is the v4.82.0 pattern (baseline first, optimize
> later) applied to async.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.93.0
**Delta review:** No
**Full panel:** No (v4.96.0)
**Estimated work:** 1 sprint
**Theme:** Measure the scheduler before tuning it. Async performance baseline vs Go.

---

## Scope

Arc 11 established the pattern: v4.82.0 was "measure everything before
changing anything." Arc 13 follows the same discipline for async. The
multi-threaded scheduler is running, but we do not know its actual
performance characteristics: task spawn overhead, suspend/resume latency,
work-stealing efficiency under contention, I/O interleaving throughput,
or backpressure behavior.

v4.94.0 ships 5 benchmark programs in `benchmarks/async/`, a Python
harness that compiles, runs, and measures each, and equivalent Go
programs for cross-language comparison. All numbers go into
machine-readable JSON and human-readable Markdown.

### Benchmark programs

Five standalone `.mn` files in `benchmarks/async/`:

1. **`sequential_chain.mn`** — 10-stage sequential await chain. Each
   stage awaits the previous. Measures per-suspend/resume overhead in
   the absence of concurrency. Baseline for the scheduler's fast path.

2. **`fan_out.mn`** — Spawn 1,000 concurrent async tasks, each computing
   a lightweight function (e.g., sum of 1..1000). Await all results.
   Measures spawn throughput (tasks/sec) and scheduler distribution.

3. **`io_bound.mn`** — 100 concurrent async file reads (small files,
   ~1KB each). Measures I/O interleaving: with real suspension, reads
   should overlap. Wall time should be close to 1 read latency, not
   100x.

4. **`mixed_cpu_io.mn`** — 50 CPU-bound tasks (fib(25)) + 50 I/O-bound
   tasks (file read). Tests scheduler fairness: CPU tasks should not
   starve I/O tasks or vice versa.

5. **`backpressure.mn`** — Producer-consumer with a bounded channel
   (capacity 10). Producer spawns 1,000 items, consumer processes each
   with a simulated delay. Measures throughput under backpressure and
   verifies no items are dropped.

Each program prints a checksum line for correctness verification plus
timing information (wall time in milliseconds).

---

## Phase 1 — Benchmark programs

- [ ] `benchmarks/async/sequential_chain.mn` — 10-stage await chain, prints stage count + total wall time
- [ ] `benchmarks/async/fan_out.mn` — spawn 1K tasks, await all, print task count + wall time + checksum
- [ ] `benchmarks/async/io_bound.mn` — 100 concurrent file reads, print file count + wall time + checksum
- [ ] `benchmarks/async/mixed_cpu_io.mn` — 50 CPU + 50 I/O tasks, print completion count + wall time
- [ ] `benchmarks/async/backpressure.mn` — bounded channel producer-consumer, print items processed + wall time
- [ ] Create test data files for I/O benchmarks: `benchmarks/async/data/` with 100 x 1KB files

## Phase 2 — Benchmark harness

- [ ] `benchmarks/async/run_async.py`:
  - Compiles each `.mn` via `python -m mapanare emit-llvm`
  - Runs through `opt -O2 -> llc -> clang link -> execute`
  - Measures per-benchmark:
    - Wall time (median of 5 runs, drop min/max)
    - Throughput (tasks/sec for fan_out, reads/sec for io_bound)
    - p50 and p99 latency (for fan_out: time per task from spawn to result)
  - Runs with thread counts: 1, 2, 4, N (where N = cores on the machine)
  - Records results as JSON: `benchmarks/async/v4.94.0-baseline.json`
  - Verifies checksum output for correctness at each thread count

## Phase 3 — Run Mapanare async benchmarks

- [ ] Execute harness on the v4.93.0 scheduler
- [ ] Save results to `benchmarks/async/v4.94.0-baseline.json`
- [ ] Verify all 5 benchmarks produce correct output at all thread counts
- [ ] Verify scaling: fan_out throughput at 4 threads > 2x throughput at 1 thread

## Phase 4 — Go comparison

- [ ] `benchmarks/async/sequential_chain.go` — 10-stage goroutine chain using channels
- [ ] `benchmarks/async/fan_out.go` — spawn 1K goroutines, WaitGroup, collect results
- [ ] `benchmarks/async/io_bound.go` — 100 concurrent file reads using goroutines
- [ ] `benchmarks/async/mixed_cpu_io.go` — 50 CPU + 50 I/O goroutines
- [ ] `benchmarks/async/backpressure.go` — buffered channel (cap 10) producer-consumer
- [ ] Run each Go benchmark with `GOMAXPROCS=1,2,4,N`
- [ ] Record in `v4.94.0-baseline.json` under `go_comparison` key

## Phase 5 — Publish results

- [ ] `benchmarks/async/ASYNC_RESULTS.md`:
  - Table 1: Mapanare at 1, 2, 4, N threads (all 5 benchmarks: wall time, throughput)
  - Table 2: Go at GOMAXPROCS=1, 2, 4, N (same 5 benchmarks)
  - Table 3: Mapanare/Go ratio per benchmark per thread count
  - Table 4: Scaling efficiency (throughput at N threads / throughput at 1 thread)
  - Narrative: where Mapanare is competitive, where it is not, and hypothesized root causes

## Phase 6 — LOW sweep + closeout

- [ ] Grep for `TODO(v4.94)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 5 async benchmark `.mn` programs exist and compile | `ls benchmarks/async/*.mn` |
| 2 | Harness runs all 5 at 1/2/4/N threads | `python benchmarks/async/run_async.py` |
| 3 | All 5 produce correct checksums at all thread counts | JSON `correct: true` |
| 4 | Baseline JSON saved | `benchmarks/async/v4.94.0-baseline.json` |
| 5 | Go comparison programs exist (5 `.go` files) | `ls benchmarks/async/*.go` |
| 6 | Go numbers recorded in JSON | `go_comparison` key in JSON |
| 7 | `ASYNC_RESULTS.md` published with all 4 tables | file exists |
| 8 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Optimize the scheduler** — this is measurement only. If fan_out is
  10x slower than Go, that is a finding, not a bug to fix in this release.
- **Change emitter or runtime code** — zero modifications to
  `emit_llvm_text.py`, `mapanare_scheduler.c`, or coroutine lowering.
- **Benchmark non-async workloads** — the optimizer benchmarks from
  v4.82.0 cover those. v4.94.0 is async-specific.
- **Rust comparison** — Go is the primary competitor for async workloads
  (goroutines are the most comparable model). Rust/Tokio comparison is
  future work.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Benchmark variance too high on WSL | medium | medium | Median of 5 runs, drop min/max. Document system specs. |
| I/O benchmark is bottlenecked by filesystem, not scheduler | medium | medium | Use tmpfs or ramdisk for test files. Record filesystem type in results. |
| Go goroutines are fundamentally faster (mature runtime) | high | low | Expected. The point is measuring the gap, not closing it. Record honestly. |
| Backpressure benchmark deadlocks | medium | medium | Timeout each run (30s). If deadlock, record as failure and investigate. |
| Thread count differences across CI machines affect results | low | medium | Record CPU model and core count in JSON. Normalize to per-thread throughput. |

---

## After v4.94.0

v4.95.0 fixes the O(n^2) string allocation pathology flagged by Mamba in the v4.51.0 review. StringBuilder in the C runtime, automatic detection in the lowerer, and AI stdlib refactoring.
