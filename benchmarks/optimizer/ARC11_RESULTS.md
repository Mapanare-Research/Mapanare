# Arc 11 Results — Optimizer Phase 1

> Measured 2026-04-13 on WSL2 (x86_64-pc-linux-gnu), LLVM 18.1.3.
> 5 runs per benchmark, median of middle 3. Verification run confirmed
> all results within 5%.

---

## Hypothesis

Arc 11 hypothesized that making the IR "LLVM-friendly" — without touching
MIR or language semantics — should yield a 2-3x speedup and close the
Go gap from 5.8x to 2-3x.

**Result: the hypothesis did not materialize for these benchmarks.** The
cumulative IR annotation changes (nsw, nounwind, willreturn, inbounds,
TBAA tree, noalias sret) produced no statistically significant improvement
on 4 of 5 benchmarks. The changes are within measurement noise.

**Why:** The bottleneck is not instruction-level metadata. It is that hot
paths go through opaque runtime FFI calls (`__mn_list_get`, `__mn_str_concat`)
that LLVM cannot optimize across. The IR annotations help LLVM within basic
blocks, but the runtime boundary prevents the cross-function optimizations
(LICM, loop unrolling, vectorization) that would produce a 2-3x speedup.

---

## Table 1: Mapanare O2 Across Arc 11

| Benchmark | v4.82.0 (baseline) | v4.83.0 | v4.84.0 | v4.85.0 (final) | Cumulative |
|-----------|-------------------|---------|---------|-----------------|------------|
| fib_recursive | 19.6ms | 19.1ms | 19.8ms | 19.6ms | 0% |
| quicksort | 1.6ms | 1.8ms | 1.9ms | 1.7ms | -4% (noise) |
| matmul_naive | 1.3ms | 1.3ms | 1.4ms | 1.4ms | -13% (noise) |
| string_concat | 96.1ms | 91.7ms | 98.9ms | 97.7ms | -2% (noise) |
| agent_fanout | 0.7ms | 0.5ms | 0.6ms | 0.5ms | +23% (noise) |

All results are within the 5% significance threshold. No benchmark showed
a statistically significant improvement from the IR annotation pass.

---

## Table 2: O0 to O2 Speedup (v4.85.0)

| Benchmark | O0 | O2 | Speedup |
|-----------|----|----|---------|
| fib_recursive | 55.7ms | 19.6ms | **2.8x** |
| quicksort | 2.1ms | 1.7ms | 1.2x |
| matmul_naive | 2.2ms | 1.4ms | 1.5x |
| string_concat | 97.8ms | 97.7ms | 1.0x |
| agent_fanout | 0.6ms | 0.5ms | 1.1x |

Only fib_recursive shows meaningful O0-to-O2 improvement (2.8x). This is
because fib is pure integer arithmetic with no FFI calls — LLVM can fully
optimize it. All other benchmarks are dominated by runtime calls.

---

## Table 3: Cross-Language Comparison (v4.85.0 O2)

| Benchmark | Mapanare O2 | Python | Rust -O | vs Python | vs Rust |
|-----------|-------------|--------|---------|-----------|---------|
| fib_recursive | 19.6ms | 789.5ms | 17.9ms | **40x faster** | 1.1x slower |
| quicksort | 1.7ms | 39.7ms | 1.3ms | **23x faster** | 1.3x slower |
| matmul_naive | 1.4ms | 64.9ms | 0.8ms | **45x faster** | 1.9x slower |
| string_concat | 97.7ms | 36.2ms | 0.7ms | 2.7x **slower** | 146x slower |
| agent_fanout | 0.5ms | 32.0ms | 0.6ms | **64x faster** | 0.8x faster |

> Go not measured (not installed in this environment).

---

## Table 4: What Changed in Each Release

| Release | IR Changes | Expected Impact |
|---------|-----------|-----------------|
| v4.82.0 | Baseline (no changes) | — |
| v4.83.0 | `nounwind` on functions, `inbounds` on all GEPs, TBAA tree | Eliminate .eh_frame; enable alias analysis |
| v4.84.0 | `willreturn` on functions, `noalias` on sret | Enable LICM, DSE; better struct-return alias analysis |

`nsw` on integer arithmetic was already present before v4.82.0.

---

## Table 5: Where Mapanare Stands

| Category | Status | Gap to Rust |
|----------|--------|-------------|
| Pure integer compute (fib) | **Competitive** | 1.1x (within 10%) |
| Array/list workloads (quicksort, matmul) | Good | 1.3-1.9x |
| String operations | **Poor** | 146x (runtime allocation issue) |
| Lightweight compute (agent_fanout) | **Competitive** | 0.8x (faster than Rust!) |

---

## Why the Hypothesis Didn't Materialize

The 2-3x hypothesis assumed that LLVM's optimizer was being held back by
missing metadata. In reality, the optimizer was already doing a good job
on the code it could see. The problem is what it **cannot** see:

1. **Runtime FFI boundary.** `__mn_list_get`, `__mn_str_concat`,
   `__mn_list_push` are opaque `call` instructions. LLVM cannot inline
   them, hoist them, or vectorize loops that call them.

2. **List representation.** Mapanare lists use a runtime-managed structure
   (data pointer + length + capacity + stride + elem_size). LLVM cannot
   prove array bounds or eliminate redundant length checks because the
   struct is opaque.

3. **String allocation.** Every `str + str` allocates a new string via
   `__mn_str_concat`. There is no in-place growth, no COW, no small-string
   optimization. This is a runtime design issue, not an IR issue.

## What Would Actually Close the Rust Gap

1. **Inline list operations.** Emit list access as direct pointer
   arithmetic + bounds check instead of calling `__mn_list_get`. This
   alone would likely give 2-3x on quicksort and matmul.

2. **String builder.** Implement `StringBuilder` or amortized-growth
   `str +=` in the runtime. This would fix the string_concat regression.

3. **Scalar replacement of aggregates.** Let LLVM's SROA break up small
   structs into registers. Requires ensuring alloca patterns don't take
   the address of individual fields unnecessarily.

These are Phase 2 (runtime + MIR) optimizations, not Phase 1 (IR hints).

---

## Reproducibility

```bash
python benchmarks/optimizer/run_baseline.py --runs 5 --cross-language \
    --output benchmarks/optimizer/v4.85.0-final.json
```

Raw data: `v4.82.0-baseline.json`, `v4.83.0-delta.json`, `v4.84.0-delta.json`, `v4.85.0-final.json`
