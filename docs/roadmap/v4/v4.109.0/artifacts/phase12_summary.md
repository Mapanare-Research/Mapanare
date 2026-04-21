# Phase 1+2 summary — LLVM pass structure + IR hint survival for optimizer benchmarks

## Pass pipeline for -O2 (LLVM 18.1.3, new PM)

See pass_pipeline.txt. The -O2 pipeline runs 70+ passes total:
  annotation2metadata -> forceattrs -> inferattrs -> coro-early ->
  function passes -> openmp-opt -> ipsccp -> globalopt ->
  cgscc(devirt(inline, function-attrs, function passes including
    sroa, early-cse, jump-threading, correlated-propagation,
    simplifycfg, instcombine, aggressive-instcombine, tailcallelim,
    reassociate, constraint-elimination, loop-mssa(loop-instsimplify,
    loop-simplifycfg, licm, loop-rotate, simple-loop-unswitch),
    loop(loop-idiom, indvars, loop-deletion, loop-unroll-full),
    vector-combine, mldst-motion, gvn, sccp, bdce, jump-threading,
    adce, memcpyopt, dse, coro-elide)) -> function-attrs ->
  deadargelim -> coro-cleanup -> globalopt -> globaldce ->
  function(float2int, lower-constant-intrinsics, loop-rotate,
    loop-deletion, loop-distribute, loop-vectorize, loop-load-elim,
    slp-vectorizer, vector-combine, loop-unroll, loop-sink,
    tailcallelim, simplifycfg) -> globaldce -> constmerge

## Hint survival across -O2

| Benchmark     | IR lines before | IR lines after | nsw before | nsw after | nuw before | nuw after | !tbaa before | !tbaa after |
|---------------|----------------:|---------------:|-----------:|----------:|-----------:|----------:|-------------:|------------:|
| fib_recursive |             147 |             79 |          3 |         4 |          0 |         0 |            0 |           0 |
| quicksort     |             466 |            380 |          9 |        13 |          0 |         1 |            0 |           0 |
| matmul_naive  |             483 |            345 |         19 |        15 |          0 |        13 |            0 |           0 |
| string_concat |             173 |             89 |          1 |         1 |          0 |         1 |            0 |           0 |

## Critical finding

**TBAA metadata is defined at module level** (`!1 = !{!"Mapanare TBAA"}`,
type nodes !2-!5, access tags !6-!9) but **NEVER attached to any load or
store instruction** across all 4 benchmarks (grep for `load .*!tbaa` or
`store .*!tbaa` returns zero matches).

The emitter's only mention of `!tbaa` is a comment at
`mapanare/emit_llvm_text.py:913`:
  "!6-!9 = access tags (used on load/store via !tbaa !N)."
— but no code actually emits `!tbaa !N` on any load/store.

Arc 11's TBAA work (v4.83.0) added the metadata tree and never wired
consumers. LLVM's alias analysis gets no type information from these
programs; TBAA has contributed exactly nothing to the measured
performance.

## LLVM-added hints at -O2

LLVM's inferFunctionAttrs and instcombine add:
- matmul_naive: 0 -> 13 nuw flags inferred (loop induction variables)
- quicksort:    0 ->  1 nuw, 9 -> 13 nsw
- function attributes: +2 to +3 per benchmark (nounwind, readonly, etc.)

LLVM's passes are inferring these hints from IR structure alone,
confirming at least part of H1: for typical integer arithmetic in
tight loops, LLVM derives the hints it needs without help from the
frontend.

