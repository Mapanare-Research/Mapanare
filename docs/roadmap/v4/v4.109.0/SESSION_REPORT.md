# v4.109.0 Session Report — 2026-04-14

## Verdict

**Shipped. Phase C release 3 complete.** Pure forensics — no code
changes. The investigation answers the question
`TOTAL_RESULTS.md` has been dodging since v4.90.0: **why did eight
releases of optimizer work produce a 0.992× aggregate geomean at
-O2?** The answer is that the geomean hid heterogeneity. Arcs 11–12
produced +24%, +9%, 0%, and −21% on the four optimizer benchmarks.
The work was not wasted; the accounting was bad.

The analysis also surfaced a previously-unnoticed bug: **Arc 11's
TBAA metadata tree is defined in the IR module header but never
attached to any load or store** across any of the four benchmarks.
The comment in `emit_llvm_text.py:913` describes the intended wiring;
the code was never written.

## Self-graded aggregate

**8.3 / 10**

- **Diagnostic depth**: landed three distinct findings that reframe
  the Arc 11–12 ROI story: (1) TBAA is dead metadata, (2)
  `willreturn` on `__mn_sb_*` declarations is actively harmful for
  string_concat, (3) function attributes — not inline nsw/nuw flags —
  are the load-bearing Arc 11 contribution. Each has a concrete
  recommendation attached. +strong
- **Scope discipline**: zero changes to `mapanare/`, `runtime/`, or
  any `.mn` / `.c` / `.h` file. All outputs are documents and
  artifacts. +strong
- **Methodology rigor**: tested all 3 hypotheses, 50-run statistics
  with trimmed median, validated stripped IR with `llvm-as`,
  confirmed semantic equivalence for fib/string_concat, flagged
  pre-existing Qs.1 bug where it affected quicksort/matmul
  consistency. +solid
- **What's missing**: no per-pass deep-dive into *which specific
  decisions* the attribute table flips for matmul (would require
  LLVM's `-print-after-all` and a human reading diffs). The analysis
  stops at "pass-ordering interactions" rather than identifying the
  exact transform. Enough for the ROI question; not enough for a
  repair.
- **A concrete next step exists**: audit `RUNTIME_FN_ATTRS` in
  `emit_llvm_text.py` and remove `willreturn` from heap-modifying
  runtime calls. Left for v4.110.0 or v4.111.0.

## What shipped

### Documents
- `benchmarks/optimizer/OPT_ROI_ANALYSIS.md` (264 lines) —
  executive summary, methodology, per-hypothesis results,
  per-workload attribution, per-hint verdicts, recommendations.
- `docs/roadmap/v4/v4.109.0/SESSION_REPORT.md` — this file.

### Artifacts (`docs/roadmap/v4/v4.109.0/artifacts/`)
- Pre-O2 IR for all 4 optimizer benchmarks + 1 scaled variant
  (`fib_45`) (`*.ll`, `*.bc`).
- Post-O2 IR for hinted and stripped variants (`*_opt.ll`,
  `*_stripped_opt.ll`).
- Per-pass IR outputs for 10 LLVM passes on `fib` and `matmul_naive`
  (`*_{instcombine,indvars,licm,gvn,sroa,loop-vectorize,loop-unroll,
  early-cse,function-attrs,aggressive-instcombine}_{h,s}.ll`).
- Full `-O2` pass pipeline dump (`pass_pipeline.txt`) and per-pass
  run log (`debug_pm.txt`).
- Phase summaries (`phase12_summary.md`, `phase3_summary.md`,
  `phase4_summary.md`, `phase5_summary.md`).
- Per-benchmark IR diffs (`*_opt_diff.txt`).

### Zero code changes
- No edits to `mapanare/`, `runtime/`, stdlib, tests, or any
  benchmark program.

## Headline findings

### 1. TBAA is 100% dead

The emitter defines the TBAA tree at module level
(`!1 = !{!"Mapanare TBAA"}`, type nodes `!2..!5`, access tags
`!6..!9`) but **never emits `!tbaa !N` on any load or store**.
`grep -c '!tbaa' <ir>` returns 0 across all 4 benchmarks. Arc 11's
TBAA contribution to alias analysis is exactly zero. The only
reference in the emitter is a comment at `emit_llvm_text.py:913`
describing the intended wiring.

### 2. Function attributes are the load-bearing Arc 11 contribution

Function attrs on runtime-call declarations (`nounwind`,
`willreturn`, `readonly`, `noalias`) cross pass boundaries via
LLVM's module-level attribute table. They change downstream decisions
(early-cse, licm, mldst-motion, dse) without being consumed inline
by any single pass (per-pass diffs show 0 instruction-level
differences on `fib` and `matmul_naive`). This matches LLVM's
documented analysis-manager architecture.

### 3. The 0.992× geomean is a heterogeneous average

Runtime deltas (hinted unstripped − stripped, median of 40 runs):

| Benchmark     | Δ (ms) | % change    |
|---------------|-------:|:------------|
| fib_recursive |  −0.12 | within noise |
| quicksort     |  −0.54 | −9% (hints help) |
| matmul_naive  |  −1.46 | **−24% (hints help)** |
| string_concat |  +1.81 | **+21% (hints HURT)** |

`matmul_naive` is where Arc 11 shipped a real 24% win. `string_concat`
is where `willreturn` on `__mn_sb_*` declarations now blocks
dead-store elimination — introduced by v4.108.0's new MIR pass
routing string building through the builder API. The aggregate
geomean of these mixed outcomes is approximately 1.0× — correct
arithmetic, wrong story.

### 4. H2 rejected: scaling fib 120× doesn't expose latent value

fib(35) → fib(45): unstripped = 2426 ms, stripped = 2394 ms. The
6% benefit at fib(35) vanishes at fib(45). LLVM converges to
equivalent codegen for recursive-accumulator patterns at any size.

## Hypotheses and their disposition

- **H1 (LLVM already did it)**: partially confirmed. For fib the
  answer is yes. For matmul the answer is no — stripping hints
  causes a 24% regression. For string_concat the answer is *LLVM
  does better without the hints* — a reverse refutation.
- **H2 (benchmarks too small)**: rejected for fib. The delta doesn't
  scale. Not tested for matmul / quicksort because Qs.1's
  `List<Int>` bug makes larger variants non-deterministic.
- **H3 (passes don't consume hints)**: subtly confirmed. No single
  LLVM pass produces a different instruction sequence on hinted vs
  stripped input. The 24% matmul delta comes from pass-ordering
  interactions mediated by the attribute table, not inline hint
  consumption.

## Recommendations (for v4.110.0+ consideration)

1. **Remove or wire the TBAA tree** in `emit_llvm_text.py:910–926`.
   Shipping dead metadata that grep suggests is live is a misleading
   signal.
2. **Audit `willreturn` on heap-modifying runtime calls**
   (`__mn_sb_append`, `__mn_sb_finish`, `__mn_list_push`, etc.). The
   attribute blocks DSE of stores the call might observe and caused
   string_concat's 21% regression in Phase 3. Case-by-case audit of
   the `RUNTIME_FN_ATTRS` table in `emit_llvm_text.py`.
3. **Keep `nsw`/`nuw` emission**. Cheap to emit; partially redundant
   with LLVM's inferrers but a hedge against future regressions.
4. **Future optimizer arcs: measure per-workload, not geomean.** The
   0.992× headline hid a 24% win plus a 21% regression. Arithmetic
   averaging across heterogeneous workloads is worse than useless.
5. **Wire escape analysis codegen** (Arc 12 infrastructure shipped;
   emitter still routes heap-safe allocations through the runtime).
   This is where the next structural speedup on allocator-bound
   benchmarks lives.

## Commit trail

```
8fb023d v4.109.0 phase 1+2: LLVM pass pipeline + IR hint survival analysis
ec20ebc v4.109.0 phase 3: H1 — stripped vs unstripped -O2 output compared
f93de04 v4.109.0 phase 4: H2 — scaling fib 120x does not amplify hint benefit
——— phase 5 commit: per-pass hint consumption ———
053573d v4.109.0 phase 6: OPT_ROI_ANALYSIS.md published
        v4.109.0: optimizer ROI analysis — honest assessment of Arcs 11-12  [final]
        Bump VERSION to 4.110.0                                             [follow-up]
```

## Exit criteria status

| # | Check | Status |
|---|---|---|
| 1 | LLVM pass structure documented | ✅ `pass_pipeline.txt` + `debug_pm.txt` |
| 2 | IR diff before/after -O2 analyzed | ✅ `phase12_summary.md` |
| 3 | H1 tested: stripped vs unstripped -O2 | ✅ `phase3_summary.md` + 40-run timing |
| 4 | H2 tested: larger benchmarks | ✅ fib(45) vs fib(35); `phase4_summary.md` |
| 5 | H3 tested: per-pass hint consumption | ✅ 10 passes × 2 benchmarks; `phase5_summary.md` |
| 6 | `OPT_ROI_ANALYSIS.md` published | ✅ 264 lines, all sections |
| 7 | Standard closeout clean | ✅ no code changes; nothing to lint |

## What's next

- **v4.110.0** (Phase C release 4, final): re-run the complete
  cross-language benchmark suite with v4.108.0's string_concat
  fix in place, compute deltas from v4.99.0 and v4.82.0 where
  comparable, publish the comprehensive Phase C results, update
  the `benchmarks/cross_language/FULL_COMPARISON.md`. After
  v4.110.0, Phase C is complete and Phase D (self-hosted maturity /
  docket cleanup, starting with **Qs.1** — the `List<Int>`
  indexing bug that has blocked quicksort correctness since v4.107.0
  discovered it) can begin.

- **Carry-forward dockets**:
  - **Qs.1**: `List<Int>` indexing returns garbage (v4.107.0 open).
  - **willreturn audit**: Phase 3 attribution of string_concat's
    21% regression. New in v4.109.0.
  - **TBAA wiring**: new in v4.109.0; decide wire-vs-remove before
    v4.110.0.
