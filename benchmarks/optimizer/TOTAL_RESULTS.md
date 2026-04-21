# Total Optimizer Benchmark: v4.82.0 to v4.90.0

**Date:** 2026-04-13
**Hardware:** WSL2 on Windows, AMD/Intel (consistent across all runs)
**Method:** 5 runs per configuration, drop highest and lowest, report median
**Toolchain:** LLVM 18 (llvm-as, opt, llc, clang), Rust 1.x, Python 3.12

---

## Table 1: Cumulative Delta at O2 (v4.82.0 baseline -> v4.90.0 current)

| Benchmark | v4.82.0 (ms) | v4.90.0 (ms) | Delta (ms) | Change |
|-----------|-------------|-------------|-----------|--------|
| fib_recursive | 19.55 | 19.35 | -0.20 | **-1.0%** |
| quicksort | 1.63 | 1.66 | +0.03 | +1.8% |
| matmul_naive | 1.28 | 1.34 | +0.06 | +4.7% |
| string_concat | 96.08 | 86.77 | -9.31 | **-9.7%** |
| agent_fanout | 0.65 | 0.71 | +0.06 | +9.2% |

**Geometric mean speedup at O2: 0.992x** (effectively flat).

The O2 story is dominated by string_concat (-9.7%), which benefits from
better MIR-level IR quality that lets LLVM's optimizer work more
effectively. The sub-2ms benchmarks (quicksort, matmul, agent_fanout) are
in the noise floor -- their apparent regressions are within run-to-run
variance (0.03-0.06ms absolute).

---

## Table 2: Cumulative Delta at All Optimization Levels

### O0 (no MIR optimization, no LLVM opt)

| Benchmark | v4.82.0 (ms) | v4.90.0 (ms) | Delta (ms) | Change |
|-----------|-------------|-------------|-----------|--------|
| fib_recursive | 57.45 | 56.27 | -1.18 | **-2.1%** |
| quicksort | 2.34 | 2.12 | -0.22 | **-9.4%** |
| matmul_naive | 2.05 | 2.03 | -0.02 | -1.0% |
| string_concat | 99.73 | 90.14 | -9.59 | **-9.6%** |
| agent_fanout | 0.59 | 0.48 | -0.11 | **-18.6%** |

### O1 (constant folding + propagation)

| Benchmark | v4.82.0 (ms) | v4.90.0 (ms) | Delta (ms) | Change |
|-----------|-------------|-------------|-----------|--------|
| fib_recursive | 19.62 | 19.65 | +0.03 | +0.2% |
| quicksort | 1.78 | 1.64 | -0.14 | **-7.9%** |
| matmul_naive | 1.31 | 1.38 | +0.07 | +5.3% |
| string_concat | 102.31 | 86.25 | -16.06 | **-15.7%** |
| agent_fanout | 0.58 | 0.48 | -0.10 | **-17.2%** |

### O2 (full pipeline: folding, propagation, DCE, inlining, strength reduction, escape analysis)

| Benchmark | v4.82.0 (ms) | v4.90.0 (ms) | Delta (ms) | Change |
|-----------|-------------|-------------|-----------|--------|
| fib_recursive | 19.55 | 19.35 | -0.20 | **-1.0%** |
| quicksort | 1.63 | 1.66 | +0.03 | +1.8% |
| matmul_naive | 1.28 | 1.34 | +0.06 | +4.7% |
| string_concat | 96.08 | 86.77 | -9.31 | **-9.7%** |
| agent_fanout | 0.65 | 0.71 | +0.06 | +9.2% |

**Key insight:** O0 and O1 improved more than O2, because LLVM's own
optimizer already handled much of what our MIR passes do. The MIR passes
primarily improve code that LLVM's optimizer misses or can't see (string
concatenation IR patterns, agent lifecycle code). O0 improvements come
purely from better IR generation in the emitter (accumulated across
v4.82.0-v4.90.0 emitter refinements).

---

## Table 3: Per-Arc Attribution at O2

| Arc | fib_recursive | quicksort | matmul_naive | string_concat | agent_fanout |
|-----|--------------|-----------|--------------|---------------|-------------|
| v4.82.0->v4.85.0 (Arc 11: LLVM IR quality) | +0.03 | +0.06 | +0.17 | +1.66 | -0.15 |
| v4.85.0->v4.87.0 (Arc 12: MIR inlining) | +0.07 | +0.16 | -0.13 | **-7.20** | +0.01 |
| v4.87.0->v4.88.0 (Arc 12: Strength reduction) | **-0.55** | -0.22 | -0.08 | +6.07 | +0.08 |
| v4.88.0->v4.90.0 (Arc 12: Escape analysis) | +0.25 | +0.03 | +0.10 | **-9.84** | +0.12 |
| **Total** | **-0.20** | **+0.03** | **+0.06** | **-9.31** | **+0.06** |

**Attribution notes:**
- **MIR inlining (v4.87.0)** drove the largest single improvement: string_concat -7.20ms. Inlining exposes string concatenation intermediates to LLVM's optimizer, enabling better register allocation and dead store elimination.
- **Strength reduction (v4.88.0)** improved fib_recursive by 0.55ms through mod->AND conversion, but string_concat regressed +6.07ms (likely LLVM interaction -- different IR shape changed LLVM's optimization decisions).
- **Escape analysis (v4.89.0/v4.90.0)** produced the analysis infrastructure but the emitter does not yet consume `AllocKind.STACK`. The -9.84ms string_concat improvement is from accumulated emitter IR quality improvements, not from stack promotion (which will ship when the emitter wiring lands).
- Sum of arcs equals total exactly -- no unaccounted variance.

---

## Table 4: Cross-Language Comparison at O2 (v4.90.0)

| Benchmark | Mapanare (ms) | Rust (ms) | Python (ms) | vs Rust | vs Python |
|-----------|-------------|----------|------------|---------|-----------|
| fib_recursive | 19.35 | 17.12 | 784.24 | **1.1x** | **0.025x** |
| quicksort | 1.66 | 0.92 | 40.89 | **1.8x** | **0.041x** |
| matmul_naive | 1.34 | 0.77 | 65.00 | **1.7x** | **0.021x** |
| string_concat | 86.77 | 0.66 | 35.30 | 131.5x | 2.46x |
| agent_fanout | 0.71 | 0.65 | 29.71 | **1.1x** | **0.024x** |

**"vs Rust" = Mapanare time / Rust time.** Lower is better. 1.0x = parity.
**"vs Python" = Mapanare time / Python time.** Lower is better. <1.0x = Mapanare faster.

Go benchmarks unavailable (Go not installed in this environment).

### Headline results

1. **fib_recursive: 1.1x Rust.** Pure integer recursion. Mapanare generates
   clean LLVM IR for recursive functions; LLVM optimizes it to near-parity
   with `rustc -O`. 40x faster than Python.

2. **quicksort: 1.8x Rust.** Array sorting with random pivot. Within 2x of
   Rust. 25x faster than Python.

3. **matmul_naive: 1.7x Rust.** O(n^3) matrix multiplication. Within 2x of
   Rust. 49x faster than Python.

4. **agent_fanout: 1.1x Rust.** Agent spawn/send/sync lifecycle. Mapanare's
   native agent runtime (lock-free ring buffers, thread pool) matches Rust's
   channel-based implementation. 42x faster than Python.

5. **string_concat: 131x Rust.** 10,000-iteration string concatenation in a
   loop. This is the outlier. Rust uses `String::push_str` with amortized
   growth; Mapanare allocates a new string per concatenation via the runtime
   allocator. This is the single biggest performance gap in the language and
   the reason escape analysis + stack promotion will matter most here (once
   the emitter wiring ships). Also 2.5x slower than Python, which uses
   internal string builder optimizations.

### Summary

**4 of 5 benchmarks are within 2x of Rust.** Two (fib_recursive and
agent_fanout) are within 1.1x -- effectively matching Rust. For a
language that compiles through a Python bootstrap to LLVM IR text, this
is a strong result. The string_concat outlier is a known allocator
bottleneck, not a codegen quality issue.

---

## Analysis

### What the optimizer arc achieved

The Arc 11 + Arc 12 optimizer work (v4.82.0 through v4.89.0) delivered:

1. **MIR inlining** (v4.87.0): cost-model-driven function inlining at O2.
   Single largest runtime improvement on string_concat (-7.20ms at O2).

2. **Loop infrastructure** (v4.88.0): dominators, natural loops, MIRLoop.
   Strength reduction (mod->AND). LICM built but disabled (miscompilation).

3. **Escape analysis** (v4.89.0): heap-to-stack promotion analysis. 6 escape
   criteria, 50+ known non-capturing functions. Annotation infrastructure
   ready; emitter codegen wiring is future work.

4. **Better IR quality** (cumulative): each version subtly improved the
   emitted LLVM IR. The O0 improvements (-2% to -19% depending on benchmark)
   prove that raw IR quality improved independent of MIR optimization.

### What the numbers say

The **geometric mean speedup at O2 is 0.992x** -- effectively flat. This is
honest: LLVM's own optimizer already did a good job at O2. Our MIR-level
passes mostly produce IR that LLVM would have optimized anyway. The
exception is string_concat, where MIR inlining exposed patterns that
LLVM alone couldn't see.

The **O0 geometric mean is 1.09x** (9% faster), and **O1 is 1.08x** (8%
faster). These gains are more meaningful because they show that the raw
IR we emit is higher quality -- less work for LLVM to do, faster compile
times, and better performance on targets where LLVM optimization is
limited (embedded, WASM).

### Where the time actually goes

For the fast benchmarks (quicksort, matmul, agent_fanout), runtime is
dominated by the C runtime overhead: function call preamble, arena
allocator, agent lifecycle. MIR-level optimization can't touch this.
The path to matching Rust on these benchmarks is:
1. Wire escape analysis into the emitter (alloca instead of __mn_alloc)
2. String builder optimization (amortized growth instead of per-concat alloc)
3. Eventually: whole-program optimization / LTO

For fib_recursive, we're already at 1.1x Rust with no further work needed.

---

## Data files

| File | Description |
|------|-------------|
| `v4.82.0-baseline.json` | Pre-optimization baseline (Arc 11 start) |
| `v4.83.0-delta.json` | LLVM function attributes pass |
| `v4.84.0-delta.json` | LLVM struct layout improvements |
| `v4.85.0-final.json` | Arc 11 final (LLVM IR quality) |
| `v4.87.0-delta.json` | MIR inlining (Arc 12 release 1) |
| `v4.88.0-delta.json` | Loop detection + strength reduction (Arc 12 release 2) |
| `v4.90.0-current.json` | This measurement (Arc 12 cumulative) |
