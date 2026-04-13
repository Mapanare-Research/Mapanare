# Mapanare v4.98.0 — Final Cross-Language Benchmark

> **Arc 14 release 2.** Comprehensive performance report covering all
> optimization work from v4.82.0 through v4.97.0. Five arcs of
> optimizer improvements, async runtime, and self-hosted propagation --
> now measured end-to-end against Python, Go, and Rust. This is the
> definitive "where does Mapanare stand" document that the v4.99.0
> panel will reference.

**Status:** DONE (2026-04-13)
**Session log:** `docs/roadmap/v4/v4.98.0/SESSION_REPORT.md`
**Decisions taken:** WSL (no bare metal); O2 only (no appendix); Python+Rust (no Go — not installed); no GPU; async compile-only (no link); prime sieve replaces list_ops (list indexing bug)
**Breaking:** No
**Prerequisite:** v4.97.0
**Delta review:** No
**Full panel:** No (v4.99.0)
**Estimated work:** 1 sprint
**Theme:** Measure everything. The numbers speak for the language.

---

## Scope

v4.82.0 established a baseline benchmark suite (5 optimizer workloads).
Arc 11 (v4.83.0-v4.85.0) improved IR quality. Arc 12 (v4.87.0-v4.91.0)
added MIR optimization passes. Arc 13 (v4.92.0-v4.96.0) shipped real
async suspension + multi-threaded scheduler. v4.97.0 propagated all
optimizations to the self-hosted compiler.

v4.98.0 brings it all together: a single comprehensive benchmark suite
that covers the full breadth of what Mapanare can do, run against the
fully-optimized self-hosted compiler, compared against three mature
languages. No new optimizations. No new features. Pure measurement
and documentation.

The output is `benchmarks/FINAL_REPORT.md` -- tables, analysis, and
headline numbers suitable for the README.

### Benchmark programs (~15 total)

Three categories:

**Optimizer benchmarks** (from v4.82.0, 5 programs):
1. `fib_recursive.mn` -- recursive Fibonacci, pure integer compute
2. `quicksort.mn` -- sort 10,000 integers, array access + recursion
3. `matmul_naive.mn` -- 128x128 matrix multiply, FP + loops
4. `string_concat.mn` -- concatenate 10,000 strings, allocation stress
5. `agent_fanout.mn` -- 1,000 messages through agent pipeline

**Async benchmarks** (from Arc 13, 5 programs):
6. `async_chain.mn` -- 10 sequential async calls, each suspending once
7. `async_fanout.mn` -- 100 concurrent coroutines, fan-out/fan-in
8. `async_io_sim.mn` -- simulated I/O with sleep-based delays, tests scheduler efficiency
9. `async_mixed.mn` -- mixed compute + async, interleaved suspension
10. `async_backpressure.mn` -- bounded channel with backpressure, producer/consumer

**System benchmarks** (new for v4.98.0, 5 programs):
11. `struct_alloc.mn` -- allocate + free 100,000 small structs, tests arena allocator
12. `enum_match.mn` -- deep enum matching over 100,000 values, tests pattern dispatch
13. `closure_capture.mn` -- 10,000 closures capturing 5 variables each, tests environment overhead
14. `list_ops.mn` -- list append/map/filter/fold over 100,000 elements
15. `compile_self.mn` -- time mnc-stage1 compiling a 1,000-line .mn program (compiler-as-benchmark)

---

## Phase 1 -- Define and validate benchmark suite

- [ ] Review existing `benchmarks/optimizer/*.mn` -- verify all 5 still compile and produce correct checksums with the v4.97.0 compiler
- [ ] Review existing `benchmarks/async/*.mn` -- verify all 5 still compile and run correctly
- [ ] Create `benchmarks/system/struct_alloc.mn` -- 100K struct alloc/free cycle, prints total + checksum
- [ ] Create `benchmarks/system/enum_match.mn` -- 100K enum values matched through 10-variant enum, prints dispatch count
- [ ] Create `benchmarks/system/closure_capture.mn` -- 10K closures with 5 captures each, invoke all, print sum
- [ ] Create `benchmarks/system/list_ops.mn` -- 100K element list, chain append/map/filter/fold, print result
- [ ] Create `benchmarks/system/compile_self.mn` -- a standalone 1,000-line .mn program for compilation timing
- [ ] Verify all 15 programs compile and produce correct output

## Phase 2 -- Run Mapanare benchmarks

- [ ] Create `benchmarks/run_final.py` -- unified harness:
  - Compiles each `.mn` via mnc-stage1 (the v4.97.0 fully-optimized self-hosted compiler)
  - Runs through `opt -O2` then `llc` then link + run
  - Measures wall-clock time (median of 5 runs, drop highest/lowest)
  - Measures peak memory via `/usr/bin/time -v` or equivalent
  - Records binary size of the linked executable
  - Counts lines of source code (for the cross-language comparison)
  - Verifies checksum output for correctness
  - Saves results as JSON: `benchmarks/v4.98.0-final.json`
- [ ] Run the harness on all 15 benchmarks
- [ ] Verify all 15 produce correct output
- [ ] Save results

## Phase 3 -- Run cross-language equivalents

- [ ] **Python 3.12** equivalents for all 15 benchmarks:
  - Optimizer benchmarks: reuse from `benchmarks/optimizer/*.py` (v4.82.0)
  - Async benchmarks: `asyncio` equivalents
  - System benchmarks: dataclass alloc, match/if-elif, closure, list comprehension, import-time
  - Measure: wall-clock time (median of 5), peak memory
- [ ] **Go 1.22** (or latest) equivalents:
  - Optimizer benchmarks: reuse from `benchmarks/optimizer/*.go`
  - Async benchmarks: goroutine equivalents
  - System benchmarks: struct alloc, switch, closure, slice ops, compile time (go build)
  - Build: `go build -o bin`; measure wall-clock + memory
- [ ] **Rust 1.78** (or latest) equivalents:
  - Optimizer benchmarks: reuse from `benchmarks/optimizer/*.rs`
  - Async benchmarks: tokio equivalents
  - System benchmarks: struct alloc, match, closure, Vec ops, compile time (rustc)
  - Build: `rustc -O -o bin`; measure wall-clock + memory
- [ ] Save all results to `benchmarks/v4.98.0-final.json` under `cross_language` key
- [ ] Verify equivalent programs produce matching checksums where applicable

## Phase 4 -- Compute comparison tables

- [ ] **Table 1: Mapanare absolute numbers** -- all 15 benchmarks, wall-clock ms, peak memory MB, binary size KB, source lines
- [ ] **Table 2: Cross-language comparison** -- 4 columns (Mapanare O2, Python, Go, Rust), all 15 benchmarks, wall-clock ms
- [ ] **Table 3: Speedup ratios** -- Mapanare/Python (how much faster), Go/Mapanare (how close to Go), Rust/Mapanare (how close to Rust)
- [ ] **Table 4: Memory comparison** -- peak memory for each language across all 15 benchmarks
- [ ] **Table 5: Binary size comparison** -- Mapanare vs Go vs Rust (Python excluded -- interpreted)
- [ ] **Table 6: Progress from baseline** -- v4.82.0 baseline vs v4.98.0 final for the 5 optimizer benchmarks (the "how far did the optimization work take us?" table)

## Phase 5 -- Publish `benchmarks/FINAL_REPORT.md`

- [ ] Write `benchmarks/FINAL_REPORT.md`:
  - **Executive summary** -- one paragraph: where Mapanare stands relative to Python, Go, Rust across 15 workloads
  - **Methodology** -- hardware specs, OS, LLVM version, compiler versions, measurement protocol (5 runs, median), how peak memory is measured
  - All 6 tables from Phase 4
  - **Analysis by category:**
    - Compute-bound (fib, quicksort, matmul): how close to Go/Rust?
    - Allocation-heavy (string, struct, list): arena allocator impact?
    - Async/concurrency (chain, fanout, io, mixed, backpressure): scheduler overhead vs goroutines vs tokio?
    - System (enum match, closure, compile time): language-level overhead?
  - **Progress narrative** -- the v4.82.0 baseline told us fib(35) was 173ms (5.8x slower than Go). What is it now? What changed and why?
  - **Known limitations** -- what benchmarks are unfair (e.g., Rust's matmul benefits from SIMD auto-vectorization that Mapanare doesn't trigger yet)
  - **Reproducibility** -- exact commands to reproduce every number

## Phase 6 -- Update README.md

- [ ] Update the performance section in `README.md` with headline numbers:
  - "Mapanare compiles to native code via LLVM. On a representative benchmark suite, it runs X-Yx faster than Python, within Xx of Go, and within Yx of Rust."
  - Link to `benchmarks/FINAL_REPORT.md` for full details
- [ ] Keep it to 3-5 sentences. The report has the details; the README has the pitch.

## Phase 7 -- LOW sweep + closeout

- [ ] Grep for `TODO(v4.98)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (9 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 15 benchmark programs exist, compile, and produce correct output | `benchmarks/v4.98.0-final.json` `correct: true` for all 15 |
| 2 | 4 languages compared (Mapanare, Python, Go, Rust) | `cross_language` key in JSON with all 4 |
| 3 | `FINAL_REPORT.md` published with all 6 tables | file exists, tables present |
| 4 | Progress from v4.82.0 baseline documented (Table 6) | table shows before/after for 5 optimizer benchmarks |
| 5 | README.md performance section updated with headline numbers | diff of README.md |
| 6 | All numbers reproducible (commands documented in FINAL_REPORT.md) | methodology section |
| 7 | Harness script runs end-to-end | `python benchmarks/run_final.py` completes |
| 8 | JSON results saved | `benchmarks/v4.98.0-final.json` exists |
| 9 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **New optimizations** -- zero changes to `mir_opt.py`, `mir_opt.mn`, `emit_llvm_text.py`, or `emit_llvm.mn`. Pure measurement.
- **New language features** -- no grammar, semantic, or runtime changes.
- **GPU benchmarks** -- GPU workloads require specific hardware. If GPU is available, include as a bonus appendix. If not, document as "future work."
- **Tune for benchmarks** -- no micro-optimization of benchmark programs to make numbers look better. Standard code, standard compilation.
- **Compare against C/C++** -- three comparison languages (Python, Go, Rust) is sufficient. C/C++ can be added in v5.x.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Benchmark variance too high on WSL | medium | medium | Median of 5 runs, drop outliers; document system specs; note WSL vs bare-metal caveat |
| Cross-language programs are not algorithmically equivalent | low | high | Code review each pair; same algorithm, same data, same checksum where applicable |
| Go or Rust not available in WSL environment | low | medium | Install via standard package managers; if unavailable, document and skip with explanation |
| The async benchmarks expose scheduler bugs under measurement load | low | medium | Run correctness check (checksum) for every measurement run; any incorrect result invalidates the run |
| Numbers look bad compared to Go/Rust | medium | low | This is data, not marketing. Report honestly. Identify why (e.g., missing SIMD, suboptimal GC-free patterns). The v4.99.0 panel grades honesty, not speed. |
| The compile-self benchmark is meaningless (too small to differentiate) | medium | low | Use a 1,000-line program with realistic features (structs, enums, functions, imports). If still too fast to differentiate, increase to 5,000 lines. |

---

## After v4.98.0

v4.99.0 is the final panel. Seven reviewers grade Arcs 10-14 holistically. The `FINAL_REPORT.md` from v4.98.0 is primary evidence for the optimization narrative. The panel decides: tag v5.0.0, continue v4.100.0+, or both. The numbers from this release are the foundation of that decision.
