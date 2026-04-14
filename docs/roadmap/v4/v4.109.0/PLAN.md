# Mapanare v4.109.0 — Optimizer ROI Investigation

> **Phase C release 3.** Arcs 11 and 12 (v4.83.0 through v4.90.0)
> added nsw/nuw flags, TBAA metadata, function attributes, MIR
> inlining, LICM, loop infrastructure, strength reduction, and escape
> analysis. The measured delta at -O2: effectively ZERO. Geometric
> mean speedup: 0.992x. fib(35) moved by 0.2ms. Why? This release
> investigates. No new optimizations. Pure forensics.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.108.0
**Delta review:** No
**Full panel:** No (numbers speak for themselves)
**Estimated work:** 1 sprint
**Theme:** Understand why 8 releases of optimization work produced zero measurable improvement at -O2.

---

## Scope

The `TOTAL_RESULTS.md` in `benchmarks/optimizer/` documents the cumulative result: geometric mean speedup at O2 is 0.992x (effectively flat). The per-arc attribution shows that every gain was offset by a regression somewhere else. The honest question that nobody has asked yet: **were Arcs 11-12 useful?**

Three hypotheses:

1. **LLVM already did it.** LLVM's -O2 is aggressive enough that nsw/nuw/TBAA/function attrs were redundant -- LLVM inferred the same information from the IR structure without the hints.

2. **The hints don't propagate.** The annotations exist in the IR but LLVM's passes don't consume them for these specific workloads. The passes that benefit (auto-vectorization, LICM) don't fire because the code structure doesn't meet their requirements.

3. **The benchmarks are wrong.** fib(35) and 10K quicksort are too small for the optimizations to produce measurable impact. The overhead of process startup, dynamic linking, and measurement noise drowns out any real improvement.

This release tests all three hypotheses and publishes an honest analysis. If the work was redundant, we say so. If it was useful groundwork for future passes, we say that too. No spin.

---

## Phase 1 -- Dump LLVM pass pipeline

- [ ] Select a representative golden test: `tests/golden/01_hello.mn` (simple) and `benchmarks/optimizer/fib_recursive.mn` (compute-intensive)
- [ ] Compile to LLVM IR: `python3 -m mapanare emit-llvm benchmarks/optimizer/fib_recursive.mn -o /tmp/fib.ll`
- [ ] Run `opt -O2 -print-pass-structure -disable-output /tmp/fib.ll 2> /tmp/pass_structure.txt` -- capture which passes run in what order
- [ ] Run `opt -O2 -debug-pass=Arguments -disable-output /tmp/fib.ll 2> /tmp/pass_args.txt` -- capture pass arguments
- [ ] Run `opt -O2 -stats -disable-output /tmp/fib.ll 2> /tmp/stats.txt` -- capture pass statistics (how many transforms each pass made)
- [ ] Document: which passes fire? Which report zero transforms? How many instructions does each pass modify?

## Phase 2 -- Compare IR before and after -O2

- [ ] Run `opt -O2 -S /tmp/fib.ll -o /tmp/fib_opt.ll`
- [ ] Diff `/tmp/fib.ll` vs `/tmp/fib_opt.ll` -- what did LLVM actually change?
- [ ] Count: how many nsw/nuw flags are in the input IR? How many in the output? Did LLVM add its own?
- [ ] Count: how many TBAA metadata references are in the input? Are they consumed by any pass?
- [ ] Count: function attributes (`nounwind`, `willreturn`, `noalias`) -- did LLVM already infer these from the IR?
- [ ] Repeat for `quicksort.mn` and `matmul_naive.mn`

## Phase 3 -- Test Hypothesis 1: LLVM already did it

- [ ] Strip all nsw/nuw flags from `/tmp/fib.ll` (sed or manual): create `/tmp/fib_stripped.ll`
- [ ] Strip all TBAA metadata
- [ ] Strip all function attributes added by Arcs 11-12
- [ ] Run `opt -O2 -S /tmp/fib_stripped.ll -o /tmp/fib_stripped_opt.ll`
- [ ] Diff `/tmp/fib_opt.ll` vs `/tmp/fib_stripped_opt.ll` -- **is the output the same?**
- [ ] If the output is identical: hypothesis 1 confirmed. LLVM infers the same optimizations without the hints.
- [ ] If the output differs: examine what's different. Quantify: how many instructions differ? In which functions?
- [ ] Benchmark both: compile `/tmp/fib_opt.ll` and `/tmp/fib_stripped_opt.ll` to binaries, measure wall-clock time

## Phase 4 -- Test Hypothesis 2: benchmarks too small

- [ ] Create larger benchmark variants:
  - `fib(45)` instead of `fib(35)` -- should be ~100x slower (exponential growth)
  - `quicksort(1M)` instead of `quicksort(10K)` -- 100x more data
  - `struct_alloc(10M)` instead of `struct_alloc(100K)` -- 100x more allocations
- [ ] Run with and without nsw/nuw/TBAA (using the stripped IR approach from Phase 3)
- [ ] Measure: does the delta become non-zero at larger scale?
- [ ] If yes: the optimizations help but only at scale beyond the benchmark's reach
- [ ] If no: the optimizations genuinely don't help for these code patterns

## Phase 5 -- Test Hypothesis 3: passes don't consume hints

- [ ] Focus on LLVM passes that should benefit from nsw/nuw: `indvars`, `loop-vectorize`, `instcombine`
- [ ] Run individual passes in isolation:
  ```bash
  opt -indvars -S /tmp/fib.ll -o /tmp/fib_indvars.ll
  opt -indvars -S /tmp/fib_stripped.ll -o /tmp/fib_stripped_indvars.ll
  diff /tmp/fib_indvars.ll /tmp/fib_stripped_indvars.ll
  ```
- [ ] Repeat for `instcombine`, `loop-vectorize`, `licm`, `gvn`
- [ ] For each pass: did nsw/nuw/TBAA change the output? If not, why?
- [ ] Look for structural reasons: are the loops too simple for vectorization? Are the memory accesses through opaque runtime calls that block alias analysis regardless of TBAA?

## Phase 6 -- Publish analysis

- [ ] Write `benchmarks/optimizer/OPT_ROI_ANALYSIS.md`:
  - **Executive summary**: one paragraph answering "were Arcs 11-12 useful?"
  - **Hypothesis 1 results**: IR diff with/without hints at -O2
  - **Hypothesis 2 results**: larger benchmarks with/without hints
  - **Hypothesis 3 results**: per-pass analysis of hint consumption
  - **Conclusion**: honest assessment. Possible conclusions:
    - "The hints were redundant for these workloads but are necessary for LTO/PGO/vectorization that LLVM would apply on larger programs"
    - "The hints are consumed but produce no runtime impact because the bottleneck is runtime function calls, not IR quality"
    - "The hints are not consumed because the IR structure (opaque runtime calls) prevents LLVM from exploiting them"
  - **Recommendations**: what (if anything) should change in future optimization arcs
  - **Raw data**: link to pass structure dumps, IR diffs, timing data

## Phase 7 -- LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.109.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (7 items)

| # | Check | Evidence |
|---|---|---|
| 1 | LLVM pass structure documented for fib_recursive at -O2 | pass_structure.txt saved or summarized |
| 2 | IR diff with/without nsw/nuw/TBAA analyzed | diff output, instruction count comparison |
| 3 | Hypothesis 1 tested: stripped IR produces same/different -O2 output | diff evidence |
| 4 | Hypothesis 2 tested: larger benchmarks show/don't show delta | timing comparison |
| 5 | Hypothesis 3 tested: individual passes consume/ignore hints | per-pass diff evidence |
| 6 | `OPT_ROI_ANALYSIS.md` published with honest conclusion | file exists, all sections present |
| 7 | Standard closeout clean | CI green |

---

## What this release does NOT do

- **Add new optimizations** -- this is forensics, not engineering. Zero changes to `mir_opt.py`, `emit_llvm_text.py`, or the runtime.
- **Judge the engineers** -- the Arc 11-12 work may have been necessary groundwork even if the benchmarks don't show it. The analysis evaluates outcomes, not effort.
- **Optimize the benchmarks** -- no changes to benchmark programs. If the benchmarks are too small, we document that; we don't inflate them to make the numbers look better.
- **Change LLVM flags** -- we're investigating why -O2 doesn't benefit from hints, not changing the optimization level.
- **Run a panel** -- Phase C has no panel.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| LLVM pass debug output format changed between versions | medium | low | Check LLVM 18 documentation for exact flags; `-debug-pass=Arguments` may be `-passes=...` in new PM |
| Stripping nsw/nuw/TBAA from IR is error-prone (might break IR validity) | medium | medium | Validate stripped IR with `llvm-as` before running opt; use sed patterns that only remove attributes, not structural tokens |
| Larger benchmarks hit timeout or memory limits in WSL | low | medium | fib(45) will take ~2 seconds (still fast); quicksort(1M) should be < 1 second. Set 120s timeout. |
| The conclusion is uncomfortable ("Arcs 11-12 were redundant") | medium | low | Report honestly. Redundant for small benchmarks != redundant forever. Frame correctly. |
| Individual pass isolation produces different results than the full pipeline | medium | low | Document this explicitly; the full pipeline has pass ordering effects that isolation misses |

---

## After v4.109.0

We now understand why the optimizer work didn't move the numbers. v4.110.0 is the final Phase C release: re-run ALL benchmarks with the string_concat fix from v4.108.0, compute deltas from v4.99.0 and v4.82.0, and publish the comprehensive Phase C results. After v4.110.0, Phase C is complete and Phase D (self-hosted maturity) begins.
