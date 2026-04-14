# Mapanare v4.112.0 — Fixed-Point Verification

> **Phase D release 2.** Self-compilation convergence: does
> stage1-from-Python produce the same output as stage1-from-self? The
> self-hosted compiler compiles itself, but Cobra flagged byref size
> heuristic divergence (docket item #7) — the self-hosted emitter returns
> 256 for all named structs while the Python bootstrap computes actual
> sizes. This release runs the 3-stage fixed-point script, identifies
> divergences, fixes the heuristic, and re-verifies.

**Status:** TODO
**Breaking:** No
**Prerequisite:** v4.111.0
**Delta review:** No
**Full panel:** No (v4.114.0)
**Estimated work:** 1 sprint
**Theme:** Fixed-point convergence — the compiler should be a fixed point of itself.

---

## Scope

The self-hosted compiler (`mapanare/self/*.mn`) compiles itself via
`bash scripts/verify_fixed_point.sh`. This script runs 3-stage
self-compilation: Python builds stage1, stage1 compiles itself to
stage2, stage2 compiles itself to stage3. If stage2 == stage3
(textual diff of emitted `.ll`), the compiler is a fixed point.

Cobra's review at v4.99.0 identified docket item #7: the self-hosted
emitter's `byref_size` function returns a hardcoded 256 for all named
struct types, while the Python bootstrap computes actual struct sizes
from field types. This means the emitted IR differs in every function
that passes structs by reference — a systematic divergence that prevents
fixed-point convergence.

This release:
1. Runs the fixed-point script and documents all divergences
2. Fixes the byref size heuristic in `mapanare/self/emit_llvm.mn`
3. Re-runs fixed-point and measures the delta
4. Records the convergence status for the v4.114.0 panel

## Phase 1 — Run fixed-point verification (baseline)

- [ ] Run `bash scripts/verify_fixed_point.sh --keep` — the `--keep` flag preserves intermediate IR for debugging
- [ ] Record result: does stage2 output match stage3 output?
- [ ] If the script itself fails (compilation error), document at which stage and why
- [ ] Save the intermediate `.ll` files for Phase 2 analysis
- [ ] Record timing: how long does the 3-stage cycle take?

## Phase 2 — Identify divergences

- [ ] Run `culebra diff stage1.ll stage2.ll` — find per-function structural differences
- [ ] Run `culebra bisect stage1.ll stage2.ll` — rank divergent functions by impact
- [ ] Classify divergences:
  - **byref size**: functions where the only difference is the byref threshold (256 vs actual) — these are item #8
  - **Semantic**: different instructions, different types, missing functions — these are new findings
  - **Cosmetic**: different temp names, block ordering — acceptable
- [ ] Count: how many functions diverge? How many are byref-only vs semantic?
- [ ] Document in `docs/roadmap/v4/v4.112.0/DIVERGENCE_ANALYSIS.md`

## Phase 3 — Fix docket item #7: byref size heuristic

- [ ] Read `mapanare/self/emit_llvm.mn` — find the `byref_size` function or equivalent that returns 256
- [ ] Read `mapanare/emit_llvm_text.py` — find the Python implementation that computes actual struct sizes
- [ ] Implement real struct size computation in the self-hosted emitter:
  - Walk the struct's field types
  - Sum field sizes (i8=1, i16=2, i32=4, i64=8, ptr=8, nested structs recurse)
  - Account for alignment padding (match the Python implementation's behavior)
- [ ] Handle edge cases: recursive structs (use pointer size), opaque types, generic instantiations
- [ ] Rebuild mnc-stage1: `bash scripts/rebuild.sh`
- [ ] Verify the fix: compile a struct-heavy golden test, check that byref annotations in the emitted IR now use correct sizes

## Phase 4 — Re-run fixed-point verification

- [ ] Run `bash scripts/verify_fixed_point.sh --keep` again with the fix applied
- [ ] Compare stage2 vs stage3: is the diff smaller?
- [ ] Run `culebra diff stage1.ll stage2.ll` again — count divergent functions
- [ ] Record delta: how many byref divergences were eliminated?
- [ ] If new divergences appeared (regression), investigate and fix
- [ ] Document results in `DIVERGENCE_ANALYSIS.md` (append "After Fix" section)

## Phase 5 — Culebra fixedpoint + golden re-test

- [ ] Run `culebra fixedpoint ./mnc-stage1 mapanare/self/mnc_all.mn` — convergence detection
- [ ] Record result: CONVERGED / DIVERGENT / ERROR
- [ ] Re-run golden tests: `python scripts/test_native.py --stage1 mapanare/self/mnc-stage1 -v`
- [ ] Verify no regressions from v4.111.0 golden count
- [ ] If golden count dropped, the byref fix introduced a regression — investigate

## Phase 6 — LOW sweep + closeout

- [ ] Standard LOW sweep
- [ ] `VERSION` bumped in final commit
- [ ] `CHANGELOG.md [4.112.0]` entry
- [ ] `SESSION_REPORT.md` written

---

## Exit criteria (10 items)

| # | Check | Evidence |
|---|---|---|
| 1 | Fixed-point script runs (3-stage self-compilation) | script output |
| 2 | Baseline divergences documented | `DIVERGENCE_ANALYSIS.md` |
| 3 | Divergences classified (byref vs semantic vs cosmetic) | classification in analysis doc |
| 4 | Docket #7 fixed: byref size computes real struct sizes | diff of `emit_llvm.mn` |
| 5 | Real struct sizes verified on struct-heavy golden test | emitted IR comparison |
| 6 | Fixed-point re-run after fix, delta recorded | script output + analysis doc |
| 7 | Culebra fixedpoint result recorded | culebra output |
| 8 | Golden tests: no regression from v4.111.0 count | test log |
| 9 | `DIVERGENCE_ANALYSIS.md` written with before/after | file |
| 10 | No new divergences introduced by the fix | culebra diff output |

---

## What this release does NOT do

- **Fix the coroutine frame coupling** — that is v4.113.0 (docket item #8).
- **Achieve full fixed-point convergence** — if semantic divergences remain beyond byref, they are documented for future work. The goal is to eliminate the #7 heuristic divergence, not necessarily all divergences.
- **Add new golden tests** — the 64-test corpus is fixed.
- **Run a panel** — the Phase D panel is v4.114.0.
- **Modify the Python bootstrap's size computation** — the Python implementation is the reference. The self-hosted emitter must match it, not the other way around.

---

## Risk register

| Risk | L | I | Mitigation |
|---|---|---|---|
| Fixed-point script fails at stage2 compilation (self-hosted can't compile itself) | medium | high | Use `--keep` to capture partial output. Debug the compilation failure as a separate issue. |
| Byref size fix changes calling convention in ways that break golden tests | medium | high | Run full golden suite after the fix. If regressions, revert and investigate the specific struct. |
| Real struct size computation is complex (alignment, padding, platform-dependent) | medium | medium | Match the Python implementation exactly. Compare output byte-for-byte on known structs. |
| Fixing byref reveals additional divergences that were masked | low | medium | Document newly visible divergences. They are pre-existing, just previously hidden by the byref noise. |
| Recursive struct types cause infinite loop in size computation | low | high | Use pointer size (8 bytes) for recursive references. The Python implementation already handles this. |

---

## After v4.112.0

v4.113.0 closes the remaining medium and low docket items: #8 (coroutine frame layout coupling), #10 (keyword collision SPEC documentation), #11 (async error messages). After v4.113.0, all medium and low docket items from the v4.99.0 panel are closed. v4.114.0 is the Phase D panel.
