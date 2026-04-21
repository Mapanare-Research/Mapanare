# Mapanare v4.91.0 — Arc 12 Panel (Optimizer Phase 2: MIR-Level)

> **Twelfth 5-minor cadence panel.** Grades Arc 12: v4.87.0 MIR
> inlining, v4.88.0 LICM + strength reduction, v4.89.0 escape
> analysis, v4.90.0 cumulative benchmark. The optimizer arc that
> followed LLVM IR quality improvements and added Mapanare-level
> transformations.
>
> Special focus: correctness. Every new optimization pass is a
> potential miscompilation vector. The panel must verify that inlining
> preserves semantics, LICM never hoists side effects, and escape
> analysis never promotes an escaping allocation.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.90.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Arc 12 closes. MIR optimizer graded for correctness, performance, and engineering quality.

---

## Arc 12 scope the panel grades

- **v4.87.0: MIR inlining pass** -- cost-model-driven function inlining (body < 20 instructions, non-recursive, budget cap 200). First interprocedural MIR optimization.
- **v4.88.0: Loop optimizations** -- natural loop detection via dominator tree, LICM (hoist invariant pure computations to preheader), strength reduction (mul->add, div->shift, mod->and).
- **v4.89.0: Escape analysis** -- non-escaping heap allocations promoted to stack allocations. Conservative escape criteria (6 conditions). ASAN-verified.
- **v4.90.0: Total optimizer benchmark** -- cumulative delta v4.82.0->v4.90.0, per-pass attribution, cross-language comparison (Go, Rust, Python). TOTAL_RESULTS.md published.

Panel-specific questions:

- **Inlining correctness:** Does the SSA renaming after cloning preserve all value identities? Are there edge cases where inlining a function with multiple return paths produces incorrect control flow?
- **LICM soundness:** Can any instruction classified as "pure" actually have side effects? Is the purity whitelist complete? Are there Mapanare-specific side effects (signal reads, stream pulls) that the whitelist misses?
- **Escape analysis soundness:** Can any non-escaping classification be wrong? Specifically: does the transitive points-to analysis handle all Copy/Phi chains? Is the "unknown call = escaping" rule applied consistently?
- **Benchmark validity:** Are the 5 benchmark programs representative of real Mapanare code? Do the cross-language comparisons use equivalent algorithms (not just equivalent problem sizes)?
- **Interaction effects:** Do the three MIR passes interact well? Does inlining always help LICM, or can it hurt (e.g., by creating very large loop bodies that slow down dominator computation)?
- **Code quality:** Is the optimizer code itself well-structured? Are the passes testable in isolation? Is the `MIRPassStats` mechanism sufficient for observability?

---

## Phase 1 — Pre-panel sweep

- [ ] Run the full test suite (`make test`) -- every test must pass
- [ ] Run all 57 golden tests at O2 -- all must pass
- [ ] Run golden tests with AddressSanitizer -- all must be ASAN-clean
- [ ] Run the optimizer stress test: compile the self-hosted compiler at O2 and verify the output IR is valid (`llvm-as` accepts it)
- [ ] Verify `benchmarks/optimizer/reproduce.sh` produces consistent results (within 5% of TOTAL_RESULTS.md)
- [ ] Grep for any `# TODO`, `# HACK`, `# FIXME` in the new optimization passes -- document or resolve

## Phase 2 — Documentation polish

- [ ] `benchmarks/optimizer/TOTAL_RESULTS.md` -- final read-through, verify all numbers are correct and tables are formatted
- [ ] Optimizer pass documentation: each new pass in `mir_opt.py` has a clear docstring explaining the algorithm, safety invariants, and limitations
- [ ] `CHANGELOG.md` entries for v4.87.0-v4.90.0 -- verify accuracy
- [ ] `docs/SPEC.md` -- update any section on optimization levels to reflect the new O2 passes

## Phase 3 — Measurement refresh

- [ ] Final benchmark run (same configuration as v4.90.0)
- [ ] `culebra summary mapanare/self/main.ll` -- record for the panel
- [ ] Optimizer pass statistics for the self-hosted compiler at O2:
  - Functions inlined
  - Invariants hoisted
  - Strengths reduced
  - Heap-to-stack promotions
  - Total instructions before/after optimization
- [ ] Record compile time: how much does the optimizer add to compilation time? (Measure with and without O2 on the self-hosted compiler)

## Phase 4 — Pre-panel audit

- [ ] Fact-check every v4.87.0-v4.90.0 SESSION_REPORT claim
- [ ] Verify that each per-release delta.json is consistent with TOTAL_RESULTS.md
- [ ] `PRE_PANEL_AUDIT.md` written

## Phase 5 — Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.91.0. Arc: Arc 12 (MIR-level optimizer).
- [ ] `mkdir -p .reviews/v4.91.0/` + pre-populate with TOTAL_RESULTS.md as primary context
- [ ] Spawn 7 reviewers. All lenses relevant to optimizer correctness:
  - **Rattler (LLVM)** -- primary. Grades inlining correctness, LICM soundness, interaction with LLVM's own optimization passes. Does MIR-level optimization conflict with or duplicate LLVM's work?
  - **Cobra (C++/ABI)** -- inlining ABI: does inlining change the calling convention or struct passing for inlined functions? Stack layout after escape analysis promotion.
  - **Mamba (C runtime)** -- benchmark validity: are the 5 programs representative? Is the measurement methodology sound? Does escape analysis interact correctly with the arena allocator?
  - **Viper (memory safety)** -- escape analysis soundness: can a promoted allocation be used after its stack frame is destroyed? Are there lifetime issues with inlined code that captures pointers to stack variables?
  - **Anaconda (toolchain)** -- pass pipeline ordering: is the O2 fixpoint loop still correct with 3 new passes? Compile time impact. CI integration of benchmarks.
  - **Boa (Python/DX)** -- optimizer observability: can a user understand what the optimizer did to their code? Are the `MIRPassStats` useful? Error messages on non-convergence.
  - **Coral (language design)** -- @noinline and @pure annotations: are these the right user-facing knobs for controlling optimization? Should there be a way to inspect optimizer decisions (like Rust's `#[inline(never)]` diagnostics)?

## Phase 6 — Closeout

- [ ] `.reviews/v4.91.0/README.md` written with panel verdict
- [ ] If PASS (aggregate >= 8.5, 0 NEEDS WORK): Arc 12 closes, proceed to Arc 13
- [ ] If NEEDS WORK: patch release v4.91.1 addressing the panel's docket
- [ ] Standard release closeout

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full test suite passes | `make test` log |
| 2 | All 57 golden tests pass at O2 | `pytest tests/golden/ -v` |
| 3 | ASAN clean on all golden tests | ASAN log |
| 4 | `reproduce.sh` produces consistent results | manual verification |
| 5 | Optimizer pass docstrings complete | code review |
| 6 | `TOTAL_RESULTS.md` numbers verified | cross-check with raw data |
| 7 | Pre-panel audit complete | `PRE_PANEL_AUDIT.md` |
| 8 | Panel prompt retargeted + pre-populated | diff + ls |
| 9 | 7 reviewer files + README.md | listed |
| 10 | Panel verdict: aggregate >= 8.5, 0 NEEDS WORK | README.md |
| 11 | `SESSION_REPORT.md` written | file |

---

## What v4.91.0 does NOT do

- **New features.** Panel release.
- **Any changes beyond docs polish + measurement refresh + panel run.**
- **Optimizer tuning based on benchmark data.** That is a post-panel activity.
- **Self-hosted mir_opt.mn update.** Tracked for a future arc.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel finds a soundness bug in escape analysis | low | critical | ASAN pre-sweep should catch UAF. If found at panel time, patch release v4.91.1 with targeted fix. |
| Panel finds LICM hoisting a side-effecting instruction | low | critical | Purity whitelist is conservative; test suite covers known cases. If found, add to whitelist exclusion and regression test. |
| Benchmark numbers disputed (methodology concerns) | medium | medium | `reproduce.sh` allows independent verification. Methodology documented in TOTAL_RESULTS.md. |
| Panel grades below 8.5 (optimizer correctness concerns) | low | high | Recovery protocol: patch release addressing specific concerns. The cadence handles this. |
| Compile time overhead from new passes is significant (> 2x) | medium | medium | Measure in Phase 3. If > 2x, document and consider gating passes behind explicit flag. |

---

## If the panel says PASS

Arc 12 closes. The MIR optimizer has inlining, LICM, strength reduction, and escape analysis -- four new passes on top of the v4.30.0 foundation of constant folding, DCE, copy propagation, branch simplification, unreachable block elimination, agent inlining, and stream fusion.

Proceed to Arc 13. Candidate themes:
- **Structured concurrency** -- task groups, supervision, cancellation tokens
- **Self-hosted compiler O2** -- port the MIR optimizer passes to `mir_opt.mn`
- **Incremental compilation** -- compile only changed modules
- **Debug information** -- DWARF for optimized code (inlined frames, promoted variables)

---

## If the panel says NEEDS WORK

Recovery protocol:
- v4.91.1 (or v4.92.0) opens as a patch release addressing the panel's docket
- Arc 12 extends until the docket is clear
- The next panel shifts accordingly

---

## After v4.91.0

If PASS: Arc 13 opens. The lead chooses the theme. Two arcs of optimizer work are complete; the compiler is measurably faster with documented evidence.
