# Phase 5 — Hypothesis 3 test: do LLVM passes consume Arc 11 hints?

## Method

Run each LLVM pass in isolation on hinted and stripped IR. Strip
cosmetic attribute-numbering differences (`#0`, `#1`), trailing
`nsw`/`nuw`/`nounwind`/`willreturn`/`noalias` tokens, and module-ID
comments from the output. Diff what remains — any surviving diff is
a real instruction-level transformation decision influenced by the
hints.

Passes tested:
- `instcombine`    (peephole optimizations, uses nsw/nuw)
- `indvars`        (induction variable simplification)
- `licm`           (loop invariant code motion)
- `gvn`            (global value numbering)
- `sroa`           (scalar replacement of aggregates)
- `loop-vectorize` (auto-vectorization)
- `loop-unroll`    (loop unrolling)
- `early-cse`      (CSE + memory analysis)
- `function-attrs` (function attribute inference)
- `aggressive-instcombine` (stronger peephole)

## Results

| Benchmark     | instcombine | indvars | licm | gvn | sroa | loop-vectorize | loop-unroll | early-cse | function-attrs | aggr-instcombine |
|---------------|:-----------:|:-------:|:----:|:---:|:----:|:--------------:|:-----------:|:---------:|:--------------:|:----------------:|
| fib           | 1           | 1       | 1    | 1   | 1    | 1              | 1           |   –       |   –            |   –              |
| matmul_naive  | 1           | 1       | 1    | 1   | 1    | 1              | 1           | 1         | 1              | 1                |

Each "1" is a single blank-line diff — i.e., *zero* meaningful
instruction-level differences.

## Interpretation

**No single LLVM pass produces a different instruction sequence
on hinted vs stripped input.** The passes preserve the hints in the
output when present, but never emit different code based on them in
isolation.

This is surprising given the 24 % runtime delta for matmul in
Phase 3 (full -O2 pipeline, hinted vs stripped). The delta must come
from **pass-ordering / interaction effects**, not from any single
pass consuming the hints:

1. An early pass (most likely `function-attrs` or `inferattrs`)
   reads the Arc 11 function attributes on runtime call declarations.
2. Subsequent passes (plausibly `early-cse`, `licm`, or
   `mldst-motion`) use that information — via the *module-level
   attribute table*, not inline instruction flags — to decide whether
   a call is hoistable, sinkable, or eliminable.
3. The end result is different codegen, but no individual pass
   transforms the IR in a way that's visible when you run that pass
   in isolation.

This is consistent with the LLVM pass manager's documented
interaction model: function attributes propagate through analysis
managers and influence downstream decisions without being consumed
by a single transform.

## Practical takeaway

- `nsw` / `nuw` on integer adds: individually consumed by passes
  that already infer them from IR structure (LLVM's
  `inferFunctionAttrs` on matmul independently produces all 13 nuw
  flags post-O2 whether the input had them or not).
- Function attributes on runtime declarations (`nounwind`,
  `willreturn`, `readonly`, `noalias`): **these are the load-bearing
  Arc 11 contribution**. They cross pass boundaries via the module-
  level attribute table and let CSE / LICM / DCE decide what's safe
  to move.
- TBAA: **never attached to any instruction** — contributes nothing
  to alias analysis in any of the 4 benchmarks. Full waste of
  emitter work at this point.
