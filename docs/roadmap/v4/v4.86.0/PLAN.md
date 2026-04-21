# Mapanare v4.86.0 — Arc 11 Panel Release (Optimizer Phase 1)

> **Eleventh 5-minor cadence panel.** Grades Arc 11: v4.82.0 baseline
> benchmarks, v4.83.0 nsw/TBAA/inbounds/mem2reg, v4.84.0 function
> attributes, v4.85.0 results publication. The panel validates that
> the IR quality improvements are correct, the measurements are
> reproducible, and the performance gains are real.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v4.85.0
**Delta review:** No
**Full panel:** **YES**
**Estimated work:** 1 sprint + external panel
**Theme:** Arc 11 closes. The optimizer phase 1 hypothesis is graded.

---

## Arc 11 scope the panel grades

- **v4.82.0**: Baseline benchmark suite (5 programs, harness, cross-language comparison)
- **v4.83.0**: nsw/nuw flags, TBAA metadata, inbounds GEPs, mem2reg-friendly allocas
- **v4.84.0**: noalias on sret + allocations, nonnull, readonly/readnone, willreturn + nounwind
- **v4.85.0**: Benchmark refresh, delta tables, cross-language gap analysis, ARC11_RESULTS.md

Panel-specific questions:
- Are the `nsw` flags semantically correct? Does Mapanare truly define integer overflow as UB, or is there an edge case?
- Is the TBAA tree correctly structured? Are there type-punning cases that violate TBAA assumptions?
- Are `noalias` annotations on `sret` parameters safe across all calling conventions?
- Are `nonnull` annotations provably correct, or are there code paths that could produce null?
- Are `readonly`/`readnone` classifications accurate for all builtins?
- Is `willreturn` safe on recursive functions?
- **Are the benchmark numbers reproducible?** Can the panel verify them independently?
- **Is the measurement methodology sound?** Median of 5, same hardware, same compiler versions?
- **Does the cross-language comparison use equivalent algorithms?** Same data, same checksums?

---

## Phase 1 -- Pre-panel sweep

- [ ] Run the full test suite: `make test` (all 4800+ tests)
- [ ] Run integration tests: all 58 golden through `llvm-as -> opt -O2 -> llc -> run`
- [ ] Verify benchmark reproducibility: re-run `run_baseline.py`, check numbers within 5% of `v4.85.0-final.json`
- [ ] Run `culebra scan mapanare/self/main.ll` -- no new critical findings
- [ ] Verify mnc-stage1 builds and passes golden tests

## Phase 2 -- Documentation polish

- [ ] `benchmarks/optimizer/ARC11_RESULTS.md` -- final read-through for accuracy
- [ ] `benchmarks/optimizer/BASELINE.md` -- verify v4.82.0 numbers still cited correctly
- [ ] `CHANGELOG.md` -- Arc 11 entry covering all 4 releases
- [ ] `README.md` performance section -- verify numbers match ARC11_RESULTS.md

## Phase 3 -- Measurement refresh

- [ ] One final benchmark run for the panel's reference
- [ ] `culebra summary mapanare/self/main.ll` -- record
- [ ] IR quality metrics:
  - Count of `nsw` annotations vs total integer arithmetic instructions
  - Count of `!tbaa` metadata vs total loads + stores
  - Count of `inbounds` GEPs vs total GEPs
  - Count of functions with `willreturn nounwind` vs total functions
- [ ] Record in `MEASUREMENTS.md`

## Phase 4 -- Pre-panel audit

- [ ] Fact-check every v4.82.0-v4.85.0 SESSION_REPORT claim
- [ ] Verify each exit criteria table was actually met (not just claimed)
- [ ] Write `.reviews/v4.86.0/PRE_PANEL_AUDIT.md`

## Phase 5 -- Panel run

- [ ] Retarget `.reviews/prompt.md` to v4.86.0. Arc: Arc 11 (optimizer phase 1).
- [ ] `mkdir -p .reviews/v4.86.0/` + pre-populate
- [ ] Spawn 7 reviewers with optimizer-specific focus:
  - **Rattler (LLVM)** -- primary. IR quality is his domain. Grades nsw/TBAA/inbounds correctness, metadata format, interaction with LLVM's pass pipeline
  - **Cobra (C++/ABI)** -- noalias/nonnull correctness across calling conventions, sret semantics
  - **Mamba (C runtime)** -- runtime performance numbers, allocation patterns, agent overhead
  - **Viper (memory safety)** -- noalias correctness (does it promise something false?), nonnull correctness (can null slip through?)
  - **Anaconda (toolchain)** -- benchmark methodology, reproducibility, cross-language fairness
  - **Boa (Python/DX)** -- developer-visible performance story, README claims
  - **Coral (language design)** -- integer overflow semantics (nsw implies UB), language-level implications
- [ ] Panel reads `ARC11_RESULTS.md` as primary evidence

## Phase 6 -- Closeout

- [ ] `.reviews/v4.86.0/README.md` written with aggregate score
- [ ] If PASS: Arc 11 closes. Proceed to Arc 12 (MIR-level optimization).
- [ ] If NEEDS WORK: address in v4.86.1 point release. Arc 11 extends.
- [ ] Standard release closeout.

---

## Exit criteria (11 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Full test suite passes (4800+ tests) | CI log |
| 2 | 58/58 golden at O2 | integration test log |
| 3 | Benchmark numbers reproducible (within 5%) | verification run |
| 4 | `ARC11_RESULTS.md` reviewed for accuracy | panel pre-read |
| 5 | IR quality metrics recorded | `MEASUREMENTS.md` |
| 6 | `PRE_PANEL_AUDIT.md` written | file |
| 7 | Panel prompt retargeted + pre-populated | diff + ls |
| 8 | 7 reviewer files + README.md | listed |
| 9 | Panel aggregate >= 8.5 | `.reviews/v4.86.0/README.md` |
| 10 | 0 NEEDS WORK verdicts | panel |
| 11 | Standard closeout clean | CI green |

---

## What v4.86.0 does NOT do

- **New features** -- panel release
- **MIR-level optimization** -- that's Arc 12
- **Additional IR changes** -- the v4.83.0-v4.84.0 changes are frozen for grading
- **Self-hosted emitter mirror** -- deferred to Arc 12

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Panel finds nsw is incorrect for some edge case | low | high | The 58 golden tests + 4800 pytest suite cover edge cases; if found, fix in v4.86.1 |
| Panel finds TBAA violates type-punning assumption | low | high | TBAA tree is coarse (no struct-level); type punning would require reinterpret_cast which Mapanare doesn't have |
| Panel finds benchmark methodology is flawed | medium | medium | Document methodology in detail; let panel suggest improvements for Arc 12 |
| Panel finds noalias on sret is unsafe for some ABI | low | medium | sret buffers are always exclusive by calling convention; Cobra will know |
| Panel aggregate < 8.5 | low | medium | If close, address feedback in v4.86.1 and re-run panel |

---

## If the panel says PASS

Arc 11 closes. The optimizer phase 1 work is validated. Proceed to
Arc 12: MIR-level optimization (constant propagation, dead code
elimination, loop strength reduction at the MIR level, before LLVM
even sees the code). Arc 12 builds on the LLVM-friendly IR from Arc 11
to achieve the full optimization pipeline.

## If the panel says NEEDS WORK

Recovery protocol:
- v4.86.1 opens as a point release addressing the panel's docket
- Arc 11 extends until all findings are resolved
- The next panel shifts to whenever the docket closes

---

## After v4.86.0

Arc 12: **MIR-Level Optimization.** With LLVM's optimizer now
effective (Arc 11), the next frontier is optimizing before LLVM: MIR
constant propagation, MIR dead code elimination, MIR loop
optimizations, MIR inlining. The goal: produce better IR in the first
place, so LLVM has even less work to do.
