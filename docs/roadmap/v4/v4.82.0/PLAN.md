# Mapanare v4.82.0 — Baseline Benchmark Suite (Optimizer Phase 1)

> **Arc 11 release 1.** Measurement-first. Before changing any IR
> emission, we establish a rigorous, reproducible baseline of how
> fast the current LLVM output actually is. Five workloads spanning
> compute, allocation, string, and concurrency. Cross-language
> comparison against Python, Go, and Rust. All numbers recorded in
> machine-readable JSON and human-readable Markdown.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.81.0
**Delta review:** No
**Full panel:** No (v4.86.0)
**Estimated work:** 1 sprint
**Theme:** You cannot optimize what you have not measured. Baseline everything.

---

## Scope

Arc 11 is "Optimizer Phase 1 -- LLVM Pass-Through." The thesis: the IR
emitted by `emit_llvm_text.py` (and `emit_llvm.mn`) is correct but
pessimistic. It lacks `nsw`/`nuw` flags, TBAA metadata, `inbounds` on
GEPs, function attributes (`noalias`, `nonnull`, `readonly`,
`willreturn`, `nounwind`), and has alloca patterns that block
`mem2reg`. As a result, `opt -O2` cannot do its job. Fixing these IR
deficiencies -- without touching MIR or the language semantics -- should
yield a 2-3x speedup.

But first: measure. v4.82.0 ships the benchmark infrastructure. No IR
changes. No optimization work. Pure measurement. This is the ruler
against which v4.83.0-v4.85.0 improvements will be judged.

Current known performance: `fib(35)` = 173ms native (vs Go 30ms, Rust
15ms, Python 1230ms). 7x faster than Python, 5.8x slower than Go.
Arc 11 aims to close the Go gap to 2-3x.

### Benchmark programs

Five standalone `.mn` files in `benchmarks/optimizer/`:

1. **`fib_recursive.mn`** -- `fib(35)` recursive. Pure integer compute.
   Stresses function call overhead + integer arithmetic.
2. **`quicksort.mn`** -- Quicksort on 10,000 random integers. Tests
   array access, swaps, recursion, branch prediction.
3. **`matmul_naive.mn`** -- Naive triple-loop matrix multiply, 128x128.
   Tests load/store patterns, loop optimization, FP arithmetic.
4. **`string_concat.mn`** -- Concatenate 10,000 short strings. Tests
   allocation, memcpy, string growth strategy.
5. **`agent_fanout.mn`** -- Fan out 1,000 messages through an agent
   pipeline. Tests runtime overhead, message passing, scheduling.

Each program prints a checksum line so correctness is verifiable.

---

## Phase 1 -- Benchmark programs

- [ ] `benchmarks/optimizer/fib_recursive.mn` -- recursive Fibonacci, prints `fib(35) = 9227465`, exits
- [ ] `benchmarks/optimizer/quicksort.mn` -- generates 10K pseudo-random ints (seeded), sorts, prints first 10 + checksum
- [ ] `benchmarks/optimizer/matmul_naive.mn` -- 128x128 float matmul of two known matrices, prints corner values + checksum
- [ ] `benchmarks/optimizer/string_concat.mn` -- concatenates "hello" 10,000 times, prints final length (50000)
- [ ] `benchmarks/optimizer/agent_fanout.mn` -- 1 producer agent, 10 worker agents, 1,000 messages, prints total processed count

## Phase 2 -- Benchmark harness

- [ ] `benchmarks/optimizer/run_baseline.py`:
  - Compiles each `.mn` via `python -m mapanare emit-llvm` (Python bootstrap path)
  - Also compiles via mnc-stage1 (self-hosted path) if available
  - Runs each through three pipelines:
    - `opt -O0` then `llc` then link + run (or `lli`)
    - `opt -O1` then `llc` then link + run
    - `opt -O2` then `llc` then link + run
  - Measures wall-clock time (median of 5 runs, with warmup)
  - Verifies checksum output for correctness
  - Records results as JSON: `{ benchmark, opt_level, median_ms, min_ms, max_ms, correct }`

## Phase 3 -- Run baselines

- [ ] Execute harness on the current (unmodified) IR
- [ ] Save results to `benchmarks/optimizer/v4.82.0-baseline.json`
- [ ] Verify all 5 benchmarks produce correct output at all 3 opt levels

## Phase 4 -- Cross-language comparison

- [ ] `benchmarks/optimizer/fib_recursive.py` / `.go` / `.rs` -- equivalent programs
- [ ] `benchmarks/optimizer/quicksort.py` / `.go` / `.rs`
- [ ] `benchmarks/optimizer/matmul_naive.py` / `.go` / `.rs`
- [ ] `benchmarks/optimizer/string_concat.py` / `.go` / `.rs`
- [ ] `benchmarks/optimizer/agent_fanout.py` / `.go` / `.rs` -- goroutines / tokio tasks / threading
- [ ] Run each, record in `benchmarks/optimizer/v4.82.0-baseline.json` under `cross_language` key
- [ ] Go: `go build -o bin && time ./bin`
- [ ] Rust: `rustc -O -o bin && time ./bin`
- [ ] Python: `time python3 prog.py`

## Phase 5 -- Publish results

- [ ] `benchmarks/optimizer/BASELINE.md`:
  - Table 1: Mapanare at O0, O1, O2 (all 5 benchmarks, median ms)
  - Table 2: Cross-language comparison (Mapanare O2 vs Python vs Go vs Rust)
  - Table 3: Speedup ratios (Mapanare/Python, Go/Mapanare, Rust/Mapanare)
  - Narrative: where Mapanare is competitive, where it isn't, and why (IR deficiency hypothesis)

## Phase 6 -- LOW sweep + closeout

- [ ] Grep for any `TODO(v4.82)` or unfinished items
- [ ] Standard closeout: `VERSION`, `CHANGELOG.md`, `SESSION_REPORT.md`

---

## Exit criteria (8 items)

| # | Check | Evidence |
|---|---|---|
| 1 | 5 benchmark `.mn` programs exist and compile | `ls benchmarks/optimizer/*.mn` |
| 2 | Harness script runs all 5 at O0/O1/O2 | `python benchmarks/optimizer/run_baseline.py` |
| 3 | All 5 produce correct checksums at all opt levels | JSON `correct: true` |
| 4 | Baseline JSON saved | `benchmarks/optimizer/v4.82.0-baseline.json` |
| 5 | Cross-language programs exist (Python, Go, Rust x 5) | `ls benchmarks/optimizer/*.{py,go,rs}` |
| 6 | Cross-language numbers recorded in JSON | `cross_language` key in JSON |
| 7 | `BASELINE.md` published with all 3 tables | file exists, tables present |
| 8 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Change IR emission** -- zero modifications to `emit_llvm_text.py` or `emit_llvm.mn`
- **Optimize anything** -- this is measurement, not improvement
- **Modify the compiler pipeline** -- no MIR changes, no new passes
- **Touch the self-hosted compiler** -- benchmark programs are standalone `.mn` files

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Benchmark variance too high on WSL | medium | medium | Use median of 5 runs; document system specs; pin CPU governor if possible |
| `lli` interpreter mode gives misleading numbers vs compiled binary | medium | high | Prefer `llc` + link to native binary; use `lli` only as fallback |
| Agent fanout benchmark is flaky due to scheduling | medium | low | Seed the RNG; verify checksum; accept 10% variance |
| Cross-language programs are not equivalent (different algorithms) | low | high | Code review each pair; same algorithm, same data, same checksum |
| `opt -O2` crashes on current IR (known pathologies) | low | medium | If crash: record as "DNF" in JSON, document the crash, fix in v4.83.0 |

---

## After v4.82.0

v4.83.0 starts the real optimization work: `nsw`/`nuw` flags, TBAA metadata, `inbounds` on GEPs, and mem2reg-friendly alloca patterns. The baseline from v4.82.0 is the ruler.
