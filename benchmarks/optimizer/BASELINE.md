# Optimizer Baseline — v4.82.0

> Measured 2026-04-13 on WSL2 (x86_64-pc-linux-gnu), LLVM 18.1.3.
> 5 runs per benchmark, median of middle 3 reported.
> Native binary via `llc -filetype=obj -relocation-model=pic` + `clang` link.

---

## Table 1: Mapanare at O0, O1, O2

| Benchmark | O0 (ms) | O1 (ms) | O2 (ms) | O0->O2 speedup |
|-----------|---------|---------|---------|-----------------|
| fib_recursive | 57.4 | 19.6 | 19.5 | 2.9x |
| quicksort | 2.3 | 1.8 | 1.6 | 1.4x |
| matmul_naive | 2.0 | 1.3 | 1.3 | 1.5x |
| string_concat | 99.7 | 102.3 | 96.1 | 1.0x |
| agent_fanout | 0.6 | 0.6 | 0.7 | 0.9x |

**Key observations:**
- **fib_recursive** shows the most improvement from O0->O2 (2.9x). Pure compute benefits from LLVM's tail-call, register allocation, and instruction scheduling.
- **string_concat** shows no improvement. The bottleneck is `__mn_str_concat` runtime calls, not the IR quality. O2 cannot optimize across FFI boundaries.
- **agent_fanout** is too fast to measure meaningfully (<1ms). The loop body is trivial.
- **quicksort** and **matmul_naive** show modest 1.4-1.5x improvement. List access via `__mn_list_get` runtime calls limits LLVM's ability to vectorize or eliminate bounds checks.

---

## Table 2: Cross-Language Comparison (at O2)

| Benchmark | Mapanare O2 (ms) | Python (ms) | Rust -O (ms) |
|-----------|-------------------|-------------|---------------|
| fib_recursive | 19.5 | 808.6 | 17.0 |
| quicksort | 1.6 | 41.7 | 1.1 |
| matmul_naive | 1.3 | 65.1 | 0.8 |
| string_concat | 96.1 | 36.2 | 0.8 |
| agent_fanout | 0.7 | 29.8 | 0.5 |

> Go not measured (not installed in this environment).

---

## Table 3: Speedup Ratios

| Benchmark | vs Python (Mn/Py) | vs Rust (Mn/Rs) |
|-----------|-------------------|-----------------|
| fib_recursive | **41x faster** | 1.1x slower |
| quicksort | **26x faster** | 1.5x slower |
| matmul_naive | **50x faster** | 1.6x slower |
| string_concat | 0.4x (2.7x **slower**) | 120x slower |
| agent_fanout | **43x faster** | 1.4x slower |

---

## Analysis

### Where Mapanare is competitive

**Pure compute** (fib_recursive): Mapanare at O2 is within 15% of Rust. The emitted IR is simple enough for LLVM to optimize effectively — recursive calls, integer arithmetic, no allocations.

**Integer workloads** (quicksort, matmul, agent_fanout): 1.1-1.6x slower than Rust. The gap is primarily from:
- List access via `__mn_list_get` runtime function (vs Rust's direct pointer arithmetic)
- Missing `nsw`/`nuw` flags preventing LLVM from proving overflow behavior
- Missing `inbounds` on GEPs preventing LLVM from proving pointer validity

### Where Mapanare is not competitive

**String concatenation**: 2.7x **slower than Python**, 120x slower than Rust. This is the worst result. The cause is clear: `__mn_str_concat` allocates a new string on every concatenation. Python's CPython has an optimization for `str += str` that reallocs in place. Rust's `String::push_str` amortizes growth. Mapanare has no string growth optimization — this is a runtime issue, not an IR issue.

### What Arc 11 IR improvements should fix

The fib, quicksort, matmul, and agent_fanout benchmarks are all within 2x of Rust. The gap is IR quality:

1. **`nsw`/`nuw` flags** on integer arithmetic — lets LLVM assume no overflow, enabling strength reduction and loop unrolling
2. **`inbounds` on GEPs** — lets LLVM prove pointer validity for alias analysis
3. **TBAA metadata** — lets LLVM prove loads/stores don't alias, enabling reordering
4. **Function attributes** (`nounwind`, `willreturn`, `noalias`) — lets LLVM eliminate dead stores and hoist invariant loads
5. **mem2reg-friendly allocas** — current alloca patterns in pre_entry block prevent SSA promotion

The string_concat regression is a **runtime issue** (not an IR issue) and is out of scope for Arc 11 optimizer work.

---

## Reproducibility

```bash
python benchmarks/optimizer/run_baseline.py --runs 5 --cross-language
```

Raw data: `v4.82.0-baseline.json`
